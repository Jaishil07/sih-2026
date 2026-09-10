import os
import tempfile
import hashlib
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from apps.cases.models import Case, CaseMember
from apps.documents.models import Document, DocumentVersion
from apps.documents.services import calculate_sha256, create_document_version, verify_document_version_integrity

User = get_user_model()

# Use a temporary directory for media during tests
TEST_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.case = Case.objects.create(case_number="CR-TEST-DOC", title="Test Case", created_by=self.user)
        self.document = Document.objects.create(case=self.case, title="Test Doc", document_type="OTHER", created_by=self.user)
        
        self.file_content = b"This is a test file content."
        self.expected_hash = hashlib.sha256(self.file_content).hexdigest()
        self.uploaded_file = SimpleUploadedFile("test.txt", self.file_content, content_type="text/plain")

    def test_calculate_sha256(self):
        file_hash = calculate_sha256(self.uploaded_file)
        self.assertEqual(file_hash, self.expected_hash)

    def test_create_document_version(self):
        version = create_document_version(self.document, self.uploaded_file, self.user, "Initial upload")
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.sha256_hash, self.expected_hash)
        
        # Second version
        file_content_v2 = b"Updated content."
        expected_hash_v2 = hashlib.sha256(file_content_v2).hexdigest()
        uploaded_file_v2 = SimpleUploadedFile("test_v2.txt", file_content_v2, content_type="text/plain")
        
        version_v2 = create_document_version(self.document, uploaded_file_v2, self.user, "Update")
        self.assertEqual(version_v2.version_number, 2)
        self.assertEqual(version_v2.sha256_hash, expected_hash_v2)

    def test_verify_integrity_success(self):
        version = create_document_version(self.document, self.uploaded_file, self.user, "Initial upload")
        self.assertTrue(verify_document_version_integrity(version))

    def test_verify_integrity_tampered(self):
        version = create_document_version(self.document, self.uploaded_file, self.user, "Initial upload")
        
        # Tamper with the file on disk
        with open(version.file.path, 'ab') as f:
            f.write(b"tampered")
            
        self.assertFalse(verify_document_version_integrity(version))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentViewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.officer_a = User.objects.create_user(username="officer_a", role=User.Role.INVESTIGATING_OFFICER, password="password")
        self.officer_b = User.objects.create_user(username="officer_b", role=User.Role.INVESTIGATING_OFFICER, password="password")
        
        self.case = Case.objects.create(case_number="CR-TEST", title="Test Case", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.officer_a, role="Investigator")
        
        self.document = Document.objects.create(case=self.case, title="Test Doc", document_type="OTHER", created_by=self.admin)
        self.uploaded_file = SimpleUploadedFile("test.txt", b"content", content_type="text/plain")
        self.version = create_document_version(self.document, self.uploaded_file, self.admin, "Initial upload")

    def test_officer_a_can_view_and_download(self):
        self.client.login(username="officer_a", password="password")
        
        # View detail
        response = self.client.get(reverse('document_detail', args=[self.document.id]))
        self.assertEqual(response.status_code, 200)
        
        # Download file
        response = self.client.get(reverse('document_download', args=[self.version.id]))
        self.assertEqual(response.status_code, 200)

    def test_officer_b_gets_403(self):
        self.client.login(username="officer_b", password="password")
        
        # View detail
        response = self.client.get(reverse('document_detail', args=[self.document.id]))
        self.assertEqual(response.status_code, 403)
        
        # Download file
        response = self.client.get(reverse('document_download', args=[self.version.id]))
        self.assertEqual(response.status_code, 403)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentRBACTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.senior = User.objects.create_user(username="senior", role=User.Role.SENIOR_OFFICER, password="password")
        self.investigator = User.objects.create_user(username="investigator", role=User.Role.INVESTIGATING_OFFICER, password="password")
        self.court_user = User.objects.create_user(username="court", role=User.Role.COURT_USER, password="password")
        
        self.case = Case.objects.create(case_number="CR-RBAC", title="RBAC Case", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.senior, role="Supervisor")
        CaseMember.objects.create(case=self.case, user=self.investigator, role="Investigator")
        CaseMember.objects.create(case=self.case, user=self.court_user, role="Judge")
        
        self.document = Document.objects.create(case=self.case, title="Evidence 1", created_by=self.admin)
        
    def test_investigating_officer_can_upload(self):
        self.client.login(username="investigator", password="password")
        response = self.client.get(reverse('document_upload', args=[self.case.id]))
        self.assertEqual(response.status_code, 200)
        
    def test_investigating_officer_cannot_delete(self):
        self.client.login(username="investigator", password="password")
        response = self.client.post(reverse('document_delete', args=[self.document.id]))
        self.assertEqual(response.status_code, 403)
        
    def test_senior_officer_can_delete(self):
        self.client.login(username="senior", password="password")
        response = self.client.post(reverse('document_delete', args=[self.document.id]))
        self.assertEqual(response.status_code, 302)  # Redirects after successful deletion
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, 'ARCHIVED')
        
    def test_court_user_cannot_upload(self):
        self.client.login(username="court", password="password")
        response = self.client.get(reverse('document_upload', args=[self.case.id]))
        self.assertEqual(response.status_code, 403)

from apps.documents.services import sign_document_version, verify_signature

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentCryptoTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin_crypto", role=User.Role.ADMIN, password="password")
        self.case = Case.objects.create(case_number="CR-CRYPTO", title="Crypto Case", created_by=self.admin)
        self.document = Document.objects.create(case=self.case, title="Top Secret Doc", created_by=self.admin)
        self.uploaded_file = SimpleUploadedFile("secret.txt", b"secret payload", content_type="text/plain")
        self.version = create_document_version(self.document, self.uploaded_file, self.admin, "Initial upload")
        
    def test_sign_and_lock_document(self):
        doc_sig = sign_document_version(self.version, self.admin)
        
        self.document.refresh_from_db()
        self.assertTrue(self.document.is_locked)
        self.assertEqual(self.document.locked_by, self.admin)
        
        self.assertTrue(verify_signature(doc_sig))
        
    def test_tampered_signature_fails(self):
        doc_sig = sign_document_version(self.version, self.admin)
        
        # Tamper signature hex
        tampered_hex = ("00" if doc_sig.signature_hex[:2] != "00" else "ff") + doc_sig.signature_hex[2:]
        doc_sig.signature_hex = tampered_hex
        doc_sig.save()
        
        self.assertFalse(verify_signature(doc_sig))
        
    def test_upload_to_locked_document_fails(self):
        sign_document_version(self.version, self.admin)
        
        uploaded_file2 = SimpleUploadedFile("secret2.txt", b"payload 2", content_type="text/plain")
        from django.core.exceptions import PermissionDenied
        
        with self.assertRaises(PermissionDenied):
            create_document_version(self.document, uploaded_file2, self.admin, "Should fail")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DocumentPreviewTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin_preview", role=User.Role.ADMIN, password="password")
        self.case = Case.objects.create(case_number="CR-PREVIEW", title="Preview Case", created_by=self.admin)
        self.document = Document.objects.create(case=self.case, title="Preview Doc", created_by=self.admin)
        self.uploaded_file = SimpleUploadedFile("preview.txt", b"preview data", content_type="text/plain")
        self.version = create_document_version(self.document, self.uploaded_file, self.admin, "Initial upload")
        
    def test_preview_endpoint(self):
        self.client.login(username="admin_preview", password="password")
        response = self.client.get(reverse('document_preview', args=[self.document.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('inline;', response['Content-Disposition'])
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_detail_view_text_preview_context(self):
        self.client.login(username="admin_preview", password="password")
        response = self.client.get(reverse('document_detail', args=[self.document.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['file_type'], 'text')
        self.assertEqual(response.context['preview_text_content'], 'preview data')

    def test_detail_view_pdf_context(self):
        self.client.login(username="admin_preview", password="password")
        pdf_file = SimpleUploadedFile("sample.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
        pdf_doc = Document.objects.create(case=self.case, title="PDF Doc", created_by=self.admin)
        create_document_version(pdf_doc, pdf_file, self.admin, "Initial upload")
        
        response = self.client.get(reverse('document_detail', args=[pdf_doc.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['file_type'], 'pdf')
        
        preview_resp = self.client.get(reverse('document_preview', args=[pdf_doc.id]))
        self.assertEqual(preview_resp.status_code, 200)
        self.assertEqual(preview_resp.headers.get('Content-Type'), 'application/pdf')
        self.assertEqual(preview_resp.headers.get('X-Frame-Options'), 'SAMEORIGIN')

    def test_detail_view_image_context(self):
        self.client.login(username="admin_preview", password="password")
        img_file = SimpleUploadedFile("sample.png", b"\x89PNG\r\n\x1a\nfakeimage", content_type="image/png")
        img_doc = Document.objects.create(case=self.case, title="Image Doc", created_by=self.admin)
        create_document_version(img_doc, img_file, self.admin, "Initial upload")
        
        response = self.client.get(reverse('document_detail', args=[img_doc.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['file_type'], 'image')
        
        preview_resp = self.client.get(reverse('document_preview', args=[img_doc.id]))
        self.assertEqual(preview_resp.status_code, 200)
        self.assertEqual(preview_resp.headers.get('Content-Type'), 'image/png')
        self.assertEqual(preview_resp.headers.get('X-Frame-Options'), 'SAMEORIGIN')
