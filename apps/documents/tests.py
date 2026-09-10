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
