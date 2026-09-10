import os
import re
from pypdf import PdfReader
from django.conf import settings
from .models import DocumentText, AIResult
from apps.audit.services import log_audit_event
from google import genai

def extract_text_from_file(file_path_or_obj, filename=""):
    """
    Extracts text from a given file object (or path).
    Supports PDF and standard text files.
    """
    text = ""
    try:
        if hasattr(file_path_or_obj, 'seek'):
            file_path_or_obj.seek(0)
            
        if filename.lower().endswith('.pdf') or (isinstance(file_path_or_obj, str) and file_path_or_obj.lower().endswith('.pdf')):
            reader = PdfReader(file_path_or_obj)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        else:
            if hasattr(file_path_or_obj, 'read'):
                content = file_path_or_obj.read()
                if isinstance(content, bytes):
                    text = content.decode('utf-8', errors='ignore')
                else:
                    text = content
            else:
                with open(file_path_or_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
    except Exception as e:
        print(f"Error extracting text: {e}")
        # Return whatever we got so far, or empty string
    finally:
        if hasattr(file_path_or_obj, 'seek'):
            file_path_or_obj.seek(0)
            
    return text.strip()

def process_document_with_ai(document, user=None):
    """
    Extracts text, uses AI to analyze it, and creates an AIResult.
    Falls back to deterministic extraction if AI fails.
    """
    # 1. Extract Text
    latest_version = document.versions.order_by('-version_number').first()
    if not latest_version or not latest_version.file:
        return None
        
    raw_text = extract_text_from_file(latest_version.file, document.title)
    
    doc_text, created = DocumentText.objects.update_or_create(
        document=document,
        defaults={'raw_text': raw_text, 'extraction_method': 'PYPDF_TEXT'}
    )
    
    if not raw_text:
        return None

    api_key = getattr(settings, 'GEMINI_API_KEY', os.environ.get('GEMINI_API_KEY'))
    
    ai_result = None
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            Analyze the following legal/investigative document and extract structured information.
            Return ONLY valid JSON matching this schema:
            {{
                "summary": "2-3 sentence executive legal summary",
                "key_findings": ["finding 1", "finding 2"],
                "entities": {{
                    "people": [],
                    "organizations": [],
                    "locations": [],
                    "dates": []
                }},
                "suggested_type": "Predicted document type (e.g. FIR, FORENSIC_REPORT, WITNESS_STATEMENT, CHARGE_SHEET, COURT_FILING)",
                "suggested_classification": "Predicted classification (e.g. INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL, PUBLIC)"
            }}
            
            Document Text:
            {raw_text[:15000]}  # limit text to avoid token limits in simple demo
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            import json
            result_data = json.loads(response.text)
            
            ai_result = AIResult.objects.create(
                document=document,
                summary=result_data.get('summary', ''),
                key_findings=result_data.get('key_findings', []),
                entities=result_data.get('entities', {}),
                suggested_type=result_data.get('suggested_type', ''),
                suggested_classification=result_data.get('suggested_classification', '')
            )
        except Exception as e:
            print(f"AI API failed: {e}")
            ai_result = None
            
    # 2. Fallback Engine
    if not ai_result:
        # Deterministic extraction
        words = raw_text.split()
        summary = " ".join(words[:300]) + ("..." if len(words) > 300 else "")
        
        # Regex for dates (YYYY-MM-DD or DD/MM/YYYY)
        dates = list(set(re.findall(r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b', raw_text)))
        
        # Basic capitalized words for people/orgs (very naive)
        caps = list(set(re.findall(r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b', raw_text)))
        
        # Filter out common words
        common = {'The', 'This', 'That', 'A', 'An', 'It', 'In', 'On', 'At', 'To', 'And'}
        caps = [c for c in caps if c not in common and len(c) > 3][:10]
        
        entities = {
            "people": caps[:5],
            "organizations": caps[5:8],
            "locations": caps[8:],
            "dates": dates
        }
        
        keywords = ["suspect", "accused", "victim", "FIR", "forensic"]
        findings = [f"Mention of {kw}" for kw in keywords if kw.lower() in raw_text.lower()]
        
        ai_result = AIResult.objects.create(
            document=document,
            summary=f"[FALLBACK EXTRACTION]\n{summary}",
            key_findings=findings if findings else ["No key keywords found."],
            entities=entities,
            suggested_type="OTHER",
            suggested_classification="INTERNAL"
        )
        
    if user:
        log_audit_event(user, 'DOCUMENT_AI_PROCESSED', 'Document', document.id)
    else:
        # If running async without user, log as System (assuming System is represented or omit user)
        pass
        
    return ai_result
