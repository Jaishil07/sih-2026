from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.cases.models import Case, PersonOfInterest
from apps.documents.models import Document, DocumentVersion
from apps.evidence.models import Evidence
from apps.ai_assistant.models import AIResult
from apps.ai_assistant.services import extract_text_from_file, process_document_with_ai

User = get_user_model()

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
        import os
        from django.conf import settings
        original_key = getattr(settings, 'GEMINI_API_KEY', None)
        if hasattr(settings, 'GEMINI_API_KEY'):
            delattr(settings, 'GEMINI_API_KEY')
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
            
        result = process_document_with_ai(doc, self.admin)
        
        self.assertIsNotNone(result)
        self.assertIn("[FALLBACK EXTRACTION]", result.summary)
        
        # Fallback regex checks
        self.assertIn("2024-05-12", result.entities.get('dates', []))
        self.assertTrue(any("suspect" in k.lower() for k in result.key_findings))
        
        if original_key:
            setattr(settings, 'GEMINI_API_KEY', original_key)

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
