from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.audit.models import AuditLog
from apps.audit.services import log_audit_event
from apps.cases.models import Case, CaseMember

User = get_user_model()

class AuditScopingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.senior = User.objects.create_user(username="senior", role=User.Role.SENIOR_OFFICER, password="password")
        self.officer_a = User.objects.create_user(username="officer_a", role=User.Role.INVESTIGATING_OFFICER, password="password", supervisor=self.senior)
        self.officer_b = User.objects.create_user(username="officer_b", role=User.Role.INVESTIGATING_OFFICER, password="password")
        
        self.case = Case.objects.create(case_number="CR-1", title="Test Case", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.officer_a, role="Investigator")

        log_audit_event(self.officer_a, 'TEST_ACTION_A', 'System', '1')
        log_audit_event(self.officer_b, 'TEST_ACTION_B', 'System', '2')

    def test_investigating_officer_cannot_see_others_logs(self):
        self.client.login(username="officer_a", password="password")
        response = self.client.get(reverse('audit_list'))
        
        logs = response.context['logs']
        actions = [log.action for log in logs]
        
        self.assertIn('TEST_ACTION_A', actions)
        self.assertNotIn('TEST_ACTION_B', actions) # Exclusive to officer_b

    def test_supervisor_can_see_subordinate_logs(self):
        self.client.login(username="senior", password="password")
        response = self.client.get(reverse('audit_list'))
        
        logs = response.context['logs']
        actions = [log.action for log in logs]
        
        # Senior supervises A but not B
        self.assertIn('TEST_ACTION_A', actions)
        self.assertNotIn('TEST_ACTION_B', actions)
