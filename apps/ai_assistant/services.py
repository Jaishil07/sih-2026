import os
import re
import json
from pypdf import PdfReader
from django.conf import settings
from .models import DocumentText, AIResult
from apps.audit.services import log_audit_event

PDF_ARTIFACT_TOKENS = {
    'pdf', 'reportlab', 'filter', 'rotate', 'mediabox', 'catalog', 'length',
    'flatedecode', 'obj', 'endobj', 'stream', 'endstream', 'xref', 'trailer',
    'startxref', 'type', 'pages', 'page', 'font', 'helvetica', 'kids', 'count',
    'parent', 'resources', 'asciihexdecode', 'ascii85decode', 'lzwdecode',
    'crypt', 'standard', 'true', 'false', 'null', 'creationdate', 'moddate',
    'producer', 'creator', 'author', 'title', 'subject', 'keywords', 'root',
    'size', 'info', 'id', 'prev', 'procset', 'extgstate'
}

STOP_WORDS = {
    'the', 'this', 'that', 'these', 'those', 'a', 'an', 'it', 'its', 'in', 'on', 'at',
    'to', 'for', 'of', 'with', 'by', 'from', 'and', 'or', 'but', 'is', 'are', 'was',
    'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'not',
    'first', 'information', 'report', 'regarding', 'incident', 'involving', 'suspect',
    'accused', 'victim', 'case', 'section', 'act', 'code', 'date', 'signed', 'state',
    'police', 'station', 'officer', 'department', 'india', 'ministry', 'court', 'under',
    'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
    'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now', 'statement', 'witness'
}

def extract_text_from_file(file_path_or_obj, filename=""):
    """
    Extracts text from a given file object or path.
    Supports PDF (via pypdf) and plain text files.
    NEVER decodes raw PDF binary bytes as string.
    Strips out null bytes and non-printable control characters.
    Returns empty string if no machine-readable text is detected.
    """
    extracted_text = ""
    
    # 1. Reset file pointer if seekable
    if hasattr(file_path_or_obj, 'seek'):
        try:
            file_path_or_obj.seek(0)
        except Exception:
            pass

    # 2. Determine file format
    fname = filename or getattr(file_path_or_obj, 'name', '')
    if not fname and isinstance(file_path_or_obj, str):
        fname = file_path_or_obj
    fname_lower = (fname or "").lower()

    # Check magic bytes if readable
    is_pdf = False
    if fname_lower.endswith('.pdf'):
        is_pdf = True
    elif hasattr(file_path_or_obj, 'read'):
        try:
            head = file_path_or_obj.read(5)
            if head.startswith(b'%PDF'):
                is_pdf = True
        except Exception:
            pass
        finally:
            if hasattr(file_path_or_obj, 'seek'):
                file_path_or_obj.seek(0)
    elif isinstance(file_path_or_obj, str) and os.path.exists(file_path_or_obj):
        try:
            with open(file_path_or_obj, 'rb') as f:
                head = f.read(5)
                if head.startswith(b'%PDF'):
                    is_pdf = True
        except Exception:
            pass

    # 3. Extract text according to format
    try:
        if is_pdf:
            # Use pypdf.PdfReader - NEVER read raw PDF bytes as string
            reader = PdfReader(file_path_or_obj)
            pages_text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)
            extracted_text = "\n".join(pages_text)
        elif fname_lower.endswith('.txt') or fname_lower.endswith('.log') or fname_lower.endswith('.csv'):
            if hasattr(file_path_or_obj, 'read'):
                raw = file_path_or_obj.read()
                if isinstance(raw, bytes):
                    extracted_text = raw.decode('utf-8', errors='ignore')
                else:
                    extracted_text = str(raw)
            elif isinstance(file_path_or_obj, str) and os.path.exists(file_path_or_obj):
                with open(file_path_or_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
        else:
            # For other/unspecified files, attempt reading as UTF-8 text only if not binary
            if hasattr(file_path_or_obj, 'read'):
                raw = file_path_or_obj.read()
                if isinstance(raw, bytes):
                    if not raw.startswith(b'%PDF'):
                        extracted_text = raw.decode('utf-8', errors='ignore')
                else:
                    extracted_text = str(raw)
            elif isinstance(file_path_or_obj, str) and os.path.exists(file_path_or_obj):
                with open(file_path_or_obj, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read()
    except Exception as e:
        print(f"Error extracting text: {e}")
        extracted_text = ""
    finally:
        if hasattr(file_path_or_obj, 'seek'):
            try:
                file_path_or_obj.seek(0)
            except Exception:
                pass

    if not extracted_text:
        return ""

    # 4. Strip out null bytes and non-printable control characters (preserving \n, \r, \t)
    extracted_text = extracted_text.replace('\x00', '')
    extracted_text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', extracted_text)

    # 5. If only whitespace, return empty string
    if not extracted_text.strip():
        return ""

    return extracted_text.strip()


def process_document_with_ai(document, user=None):
    """
    Extracts text, uses Gemini API to analyze it (with strict schema),
    and creates an AIResult. Falls back to deterministic local extraction
    if Gemini API key is not configured or network call fails.
    """
    # 1. Retrieve latest document version
    latest_version = document.versions.order_by('-version_number').first()
    if not latest_version or not latest_version.file:
        return None

    filename = getattr(latest_version.file, 'name', '') or document.title
    raw_text = extract_text_from_file(latest_version.file, filename)

    # Persist extracted text record
    DocumentText.objects.update_or_create(
        document=document,
        defaults={'raw_text': raw_text, 'extraction_method': 'PYPDF_TEXT'}
    )

    api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
    ai_result = None

    # 2. Attempt Gemini API Call if configured and text is meaningful
    if api_key and len(api_key.strip()) > 10 and not api_key.startswith('your_') and len(raw_text.strip()) >= 20:
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            prompt = f"""
Analyze the following legal/investigative document and extract structured intelligence.
Return ONLY valid JSON matching this schema:
{{
    "summary": "2-3 sentence executive legal summary",
    "key_findings": ["finding 1", "finding 2"],
    "entities": {{
        "people": ["Full Name 1"],
        "organizations": ["Organization 1"],
        "locations": ["Location 1"],
        "dates": ["Date 1"]
    }},
    "suggested_type": "Predicted document type (e.g. FIR, FORENSIC_REPORT, WITNESS_STATEMENT, CHARGE_SHEET, COURT_FILING, OTHER)",
    "suggested_classification": "Predicted classification (e.g. INTERNAL, CONFIDENTIAL, HIGHLY_CONFIDENTIAL, PUBLIC)"
}}

Document Text:
{raw_text[:15000]}
"""
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            result_data = json.loads(response.text)
            entities_data = result_data.get('entities', {})
            if not isinstance(entities_data, dict):
                entities_data = {}

            cleaned_entities = {
                'people': [str(p) for p in entities_data.get('people', []) if str(p).lower() not in PDF_ARTIFACT_TOKENS],
                'organizations': [str(o) for o in entities_data.get('organizations', []) if str(o).lower() not in PDF_ARTIFACT_TOKENS],
                'locations': [str(l) for l in entities_data.get('locations', [])],
                'dates': [str(d) for d in entities_data.get('dates', [])]
            }

            ai_result = AIResult.objects.create(
                document=document,
                summary=str(result_data.get('summary', '')).strip(),
                key_findings=list(result_data.get('key_findings', [])),
                entities=cleaned_entities,
                suggested_type=result_data.get('suggested_type', 'OTHER') or 'OTHER',
                suggested_classification=result_data.get('suggested_classification', 'INTERNAL') or 'INTERNAL'
            )
        except Exception as e:
            print(f"Gemini API execution failed: {e}. Falling back to deterministic extractor.")
            ai_result = None

    # 3. Robust Fallback Engine (when API key missing, network fails, or text is minimal)
    if not ai_result:
        clean_text = raw_text.strip()
        
        # Subcase A: Empty or less than 20 characters
        if len(clean_text) < 20:
            ai_result = AIResult.objects.create(
                document=document,
                summary="No machine-readable text detected. Document may be a scanned image or empty.",
                key_findings=["Manual review required: No digital text found."],
                entities={"people": [], "organizations": [], "locations": [], "dates": []},
                suggested_type="OTHER",
                suggested_classification="INTERNAL"
            )
        else:
            # Subcase B: Valid text exists (>= 20 characters)
            # Extractive summary using first 2-3 genuine sentences
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 10]
            if sentences:
                extractive_body = " ".join(sentences[:3])
            else:
                words = clean_text.split()
                extractive_body = " ".join(words[:50]) + ("..." if len(words) > 50 else "")
            
            summary = f"[Local Extractive Analysis]\n{extractive_body}"

            # Date extraction via regex
            date_pattern = r'\b\d{4}-\d{2}-\d{2}\b|\b\d{2}/\d{2}/\d{4}\b|\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b'
            extracted_dates = list(dict.fromkeys(re.findall(date_pattern, clean_text, re.IGNORECASE)))

            # Entity candidate extraction: capitalized phrases
            caps_candidates = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', clean_text)
            
            filtered_entities = []
            for c in caps_candidates:
                c_clean = c.strip()
                c_lower = c_clean.lower()
                tokens = c_lower.split()

                # Filter out any PDF artifact tokens (case-insensitive)
                if any(t in PDF_ARTIFACT_TOKENS for t in tokens):
                    continue
                # Filter out common stop-word phrases
                if all(t in STOP_WORDS for t in tokens):
                    continue
                # If candidate is a date or inside an extracted date, skip
                if any(c_clean.lower() in d.lower() for d in extracted_dates):
                    continue
                if len(c_clean) < 3:
                    continue
                if c_clean not in filtered_entities:
                    filtered_entities.append(c_clean)

            people = []
            organizations = []
            locations = []

            for ent in filtered_entities:
                lower_ent = ent.lower()
                if any(kw in lower_ent for kw in ['ltd', 'corp', 'inc', 'bank', 'ministry', 'bureau', 'agency', 'dept', 'department', 'board', 'commission']):
                    organizations.append(ent)
                elif any(kw in lower_ent for kw in ['delhi', 'mumbai', 'bangalore', 'kolkata', 'chennai', 'hyderabad', 'pune', 'road', 'nagar', 'city', 'district', 'state', 'india']):
                    locations.append(ent)
                else:
                    people.append(ent)

            entities = {
                "people": people[:5],
                "organizations": organizations[:5],
                "locations": locations[:5],
                "dates": extracted_dates[:5]
            }

            keywords = ["suspect", "accused", "victim", "fir", "forensic", "investigation", "incident", "evidence", "cyber"]
            findings = [f"Mention of {kw.upper()}" for kw in keywords if kw.lower() in clean_text.lower()]
            if not findings:
                findings = ["Document analyzed locally. Investigation keywords reviewed."]

            # Suggested document type
            lower_clean = clean_text.lower()
            if "first information report" in lower_clean or " fir " in f" {lower_clean} ":
                suggested_type = "FIR"
            elif "forensic" in lower_clean:
                suggested_type = "FORENSIC_REPORT"
            elif "witness" in lower_clean or "statement" in lower_clean:
                suggested_type = "WITNESS_STATEMENT"
            elif "charge sheet" in lower_clean:
                suggested_type = "CHARGE_SHEET"
            elif "court" in lower_clean or "petition" in lower_clean or "judgment" in lower_clean:
                suggested_type = "COURT_FILING"
            else:
                suggested_type = "OTHER"

            ai_result = AIResult.objects.create(
                document=document,
                summary=summary,
                key_findings=findings,
                entities=entities,
                suggested_type=suggested_type,
                suggested_classification="INTERNAL"
            )

    if user:
        log_audit_event(user, 'DOCUMENT_AI_PROCESSED', 'Document', document.id)

    return ai_result
