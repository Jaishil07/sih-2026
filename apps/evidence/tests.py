from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.cases.models import Case, CaseMember
from apps.evidence.models import Evidence, CustodyTransfer

User = get_user_model()

class EvidenceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.officer_a = User.objects.create_user(username="officer_a", role=User.Role.INVESTIGATING_OFFICER, password="password")
        self.officer_b = User.objects.create_user(username="officer_b", role=User.Role.INVESTIGATING_OFFICER, password="password")
        
        self.case = Case.objects.create(case_number="CR-EVIDENCE", title="Test", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.officer_a, role="Investigator")

    def test_evidence_creation_and_transfer(self):
        self.client.login(username="officer_a", password="password")
        
        # Create evidence
        response = self.client.post(reverse('evidence_create', args=[self.case.id]), {
            'evidence_number': 'EV-001',
            'description': 'Laptop'
        })
        
        evidence = Evidence.objects.get(evidence_number='EV-001')
        self.assertEqual(evidence.current_custodian, self.officer_a)
        
        # Check initial transfer record
        initial_transfer = CustodyTransfer.objects.get(evidence=evidence)
        self.assertEqual(initial_transfer.to_user, self.officer_a)
        
        # Transfer custody to admin
        response = self.client.post(reverse('evidence_detail', args=[evidence.id]), {
            'to_user': self.admin.id,
            'reason': 'Lab Analysis',
            'location': 'Forensic Lab'
        })
        
        # Accept custody as admin
        transfer = CustodyTransfer.objects.last()
        self.client.login(username="admin", password="password")
        self.client.post(reverse('accept_custody_transfer', args=[transfer.id]))
        
        evidence.refresh_from_db()
        self.assertEqual(evidence.current_custodian, self.admin)
        self.assertEqual(CustodyTransfer.objects.count(), 2)

    def test_unauthorized_user_cannot_access_evidence(self):
        # Create evidence as admin
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-002', description='Phone')
        
        self.client.login(username="officer_b", password="password")
        response = self.client.get(reverse('evidence_detail', args=[evidence.id]))
        self.assertEqual(response.status_code, 403)

    def test_evidence_approval_workflow(self):
        # Admin creates evidence
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-003', description='Tablet', current_custodian=self.officer_a)
        
        # Default status is PENDING_APPROVAL
        self.assertEqual(evidence.status, Evidence.Status.PENDING_APPROVAL)
        
        # Investigating officer tries to approve
        self.client.login(username="officer_a", password="password")
        response = self.client.post(reverse('approve_evidence', args=[evidence.id]), {
            'action': 'approve',
            'notes': 'Looks good'
        })
        evidence.refresh_from_db()
        self.assertEqual(evidence.status, Evidence.Status.PENDING_APPROVAL) # Fails due to permissions
        
        # Senior Officer/Admin tries to approve
        self.client.login(username="admin", password="password")
        response = self.client.post(reverse('approve_evidence', args=[evidence.id]), {
            'action': 'approve',
            'notes': 'Approved by Admin'
        })
        
        evidence.refresh_from_db()
        self.assertEqual(evidence.status, Evidence.Status.APPROVED)
        self.assertEqual(evidence.approved_by, self.admin)
        self.assertEqual(evidence.approval_notes, 'Approved by Admin')

    def test_custody_transfer_workflow(self):
        # Admin creates evidence
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-004', description='Laptop', current_custodian=self.officer_a)
        
        # officer_a initiates transfer to officer_b
        self.client.login(username="officer_a", password="password")
        response = self.client.post(reverse('evidence_detail', args=[evidence.id]), {
            'to_user': self.officer_b.id,
            'reason': 'Lab Analysis',
            'location': 'Forensic Lab 1'
        })
        
        evidence.refresh_from_db()
        # Custodian should still be officer_a
        self.assertEqual(evidence.current_custodian, self.officer_a)
        
        transfer = CustodyTransfer.objects.last()
        self.assertEqual(transfer.status, CustodyTransfer.Status.PENDING)
        self.assertEqual(transfer.to_user, self.officer_b)
        
        # officer_b accepts
        self.client.login(username="officer_b", password="password")
        response = self.client.post(reverse('accept_custody_transfer', args=[transfer.id]))
        
        evidence.refresh_from_db()
        transfer.refresh_from_db()
        
        self.assertEqual(transfer.status, CustodyTransfer.Status.ACCEPTED)
        self.assertEqual(evidence.current_custodian, self.officer_b)
