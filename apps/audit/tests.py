from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.audit.models import AuditLog
from apps.audit.services import log_audit_event, verify_audit_chain, calculate_event_hash
import json
from django.utils import timezone

User = get_user_model()

class AuditChainTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

    def test_genesis_event_hash(self):
        log = log_audit_event(self.user, "LOGIN_SUCCESS", "User", self.user.id)
        self.assertEqual(log.previous_hash, "0" * 64)
        
        expected = calculate_event_hash(
            str(self.user.id), "LOGIN_SUCCESS", "User", str(self.user.id),
            log.timestamp.strftime('%Y-%m-%dT%H:%M:%S'), "0" * 64, json.dumps({}, sort_keys=True)
        )
        self.assertEqual(log.event_hash, expected)

    def test_chaining_and_verification(self):
        log1 = log_audit_event(self.user, "LOGIN_SUCCESS", "User", self.user.id)
        log2 = log_audit_event(self.user, "DOCUMENT_UPLOADED", "Document", 1)
        
        self.assertEqual(log2.previous_hash, log1.event_hash)
        
        is_valid, broken_id = verify_audit_chain()
        self.assertTrue(is_valid)
        self.assertIsNone(broken_id)

    def test_tamper_detection(self):
        log1 = log_audit_event(self.user, "LOGIN_SUCCESS", "User", self.user.id)
        log2 = log_audit_event(self.user, "DOCUMENT_UPLOADED", "Document", 1)
        log3 = log_audit_event(self.user, "VERSION_CREATED", "DocumentVersion", 2)
        
        # Tamper with log2 action
        AuditLog.objects.filter(id=log2.id).update(action="TAMPERED")
        
        is_valid, broken_id = verify_audit_chain()
        self.assertFalse(is_valid)
        self.assertEqual(broken_id, log2.id)
