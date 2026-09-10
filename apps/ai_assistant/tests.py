import io
import os
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pypdf import PdfReader, PdfWriter
from apps.cases.models import Case, PersonOfInterest
from apps.documents.models import Document, DocumentVersion
from apps.ai_assistant.models import AIResult
from apps.ai_assistant.services import extract_text_from_file, process_document_with_ai

User = get_user_model()

def create_dummy_pdf():
    import zlib
    stream_data = b'''BT
/F1 12 Tf
72 712 Td
(First Information Report regarding cyber incident on 10 September 2026 involving suspect Vikram.) Tj
ET'''
    compressed = zlib.compress(stream_data)

    raw_pdf = f'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {len(compressed)} /Filter /FlateDecode >>
stream
'''.encode('latin1') + compressed + b'''
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000228 00000 n 
0000000307 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
500
%%EOF'''
    reader = PdfReader(io.BytesIO(raw_pdf))
    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class AIAssistantTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.officer_a = User.objects.create_user(username="officer_a", role=User.Role.INVESTIGATING_OFFICER, password="password")
        self.officer_b = User.objects.create_user(username="officer_b", role=User.Role.INVESTIGATING_OFFICER, password="password")
        
        self.case = Case.objects.create(case_number="CR-1", title="Cyber Extortion", created_by=self.admin)
        self.case.members.create(user=self.officer_a, role="Lead")
        
        # Another case that officer_b has access to, but officer_a doesn't
        self.case_b = Case.objects.create(case_number="CR-2", title="Theft", created_by=self.admin)
        self.case_b.members.create(user=self.officer_b, role="Lead")

    def test_fallback_ai_extraction(self):
        # Create a document
        doc = Document.objects.create(case=self.case, title="Suspect Statement", document_type="WITNESS_STATEMENT", created_by=self.admin)
        
        test_content = b"The suspect Vikram Malhotra was seen on 2024-05-12 in New Delhi plotting a cyber intrusion."
        file = SimpleUploadedFile("statement.txt", test_content, content_type="text/plain")
        
        version = DocumentVersion.objects.create(document=doc, version_number=1, created_by=self.admin, change_reason="Initial", file=file)
        
        # Test extraction manually
        text = extract_text_from_file(version.file, "statement.txt")
        self.assertIn("Vikram Malhotra", text)
        
        # Process without API key (forces fallback)
        original_key = getattr(settings, 'GEMINI_API_KEY', None)
        if hasattr(settings, 'GEMINI_API_KEY'):
            delattr(settings, 'GEMINI_API_KEY')
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
            
        result = process_document_with_ai(doc, self.admin)
        
        self.assertIsNotNone(result)
        self.assertIn("[Local Extractive Analysis]", result.summary)
        
        # Fallback regex checks
        self.assertIn("2024-05-12", result.entities.get('dates', []))
        self.assertTrue(any("suspect" in k.lower() for k in result.key_findings))
        
        if original_key:
            setattr(settings, 'GEMINI_API_KEY', original_key)

    def test_pdf_text_extraction_and_ai_processing(self):
        pdf_bytes = create_dummy_pdf()
        
        # 1. Test extraction from dummy PDF
        file_obj = SimpleUploadedFile("fir_report.pdf", pdf_bytes, content_type="application/pdf")
        extracted_text = extract_text_from_file(file_obj, "fir_report.pdf")
        
        # Asserts that extract_text_from_file contains 'First Information Report' and does NOT contain '%PDF-1.4' or '/Filter'
        self.assertIn("First Information Report", extracted_text)
        self.assertNotIn("%PDF-1.4", extracted_text)
        self.assertNotIn("/Filter", extracted_text)
        
        # 2. Test document processing with AI (without API key -> fallback)
        original_key = getattr(settings, 'GEMINI_API_KEY', None)
        if hasattr(settings, 'GEMINI_API_KEY'):
            delattr(settings, 'GEMINI_API_KEY')
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
            
        doc = Document.objects.create(
            case=self.case,
            title="FIR Cyber Report",
            document_type="FIR",
            created_by=self.admin
        )
        version = DocumentVersion.objects.create(
            document=doc,
            version_number=1,
            created_by=self.admin,
            change_reason="Initial FIR Upload",
            file=SimpleUploadedFile("fir_report.pdf", pdf_bytes, content_type="application/pdf")
        )
        
        result = process_document_with_ai(doc, self.admin)
        self.assertIsNotNone(result)
        
        # Asserts that process_document_with_ai does not extract PDF internal dictionary keys into entities['people']
        self.assertIn("Vikram", result.entities.get('people', []))
        
        forbidden_tokens = ['PDF', 'ReportLab', 'Filter', 'Rotate', 'MediaBox', 'Catalog', 'Length', 'FlateDecode', 'Obj', 'Endobj']
        for token in forbidden_tokens:
            self.assertNotIn(token, result.entities.get('people', []), f"PDF artifact token '{token}' should not be in entities['people']")
            self.assertNotIn(token, result.entities.get('organizations', []), f"PDF artifact token '{token}' should not be in entities['organizations']")

        if original_key:
            setattr(settings, 'GEMINI_API_KEY', original_key)

    def test_empty_or_scanned_pdf_fallback(self):
        doc = Document.objects.create(case=self.case, title="Scanned Doc", created_by=self.admin)
        file = SimpleUploadedFile("scanned.txt", b"", content_type="text/plain")
        DocumentVersion.objects.create(document=doc, version_number=1, created_by=self.admin, file=file)
        
        result = process_document_with_ai(doc, self.admin)
        self.assertIsNotNone(result)
        self.assertEqual(result.summary, "No machine-readable text detected. Document may be a scanned image or empty.")
        self.assertEqual(result.key_findings, ["Manual review required: No digital text found."])
        self.assertEqual(result.entities, {"people": [], "organizations": [], "locations": [], "dates": []})

    def test_global_search_visibility(self):
        # Create searchable POI in case A
        poi = PersonOfInterest.objects.create(case=self.case, name="ShadowByte", role_in_case="SUSPECT")
        
        # Create searchable Document in case B
        doc = Document.objects.create(case=self.case_b, title="Forensic SSD Report", document_type="FORENSIC_REPORT", created_by=self.admin)
        
        # Admin can search everything
        self.client.login(username="admin", password="password")
        response = self.client.get(reverse('global_search') + "?q=ShadowByte")
        self.assertContains(response, "ShadowByte")
        
        response = self.client.get(reverse('global_search') + "?q=Forensic SSD Report")
        self.assertContains(response, "Forensic SSD Report")
        
        # Officer A can search Case A stuff
        self.client.login(username="officer_a", password="password")
        response = self.client.get(reverse('global_search') + "?q=ShadowByte")
        self.assertContains(response, "ShadowByte")
        
        # Officer A CANNOT search Case B stuff
        response = self.client.get(reverse('global_search') + "?q=Forensic SSD Report")
        self.assertEqual(len(response.context['results']['documents']), 0)
        self.assertContains(response, "No matches found in your assigned cases.")
