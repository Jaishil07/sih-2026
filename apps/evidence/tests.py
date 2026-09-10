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
        response = self.client.post(reverse('evidence:evidence_create', args=[self.case.id]), {
            'evidence_number': 'EV-001',
            'description': 'Laptop'
        })
        
        evidence = Evidence.objects.get(evidence_number='EV-001')
        self.assertEqual(evidence.current_custodian, self.officer_a)
        
        # Check initial transfer record
        initial_transfer = CustodyTransfer.objects.get(evidence=evidence)
        self.assertEqual(initial_transfer.to_user, self.officer_a)
        
        # Transfer custody to admin
        response = self.client.post(reverse('evidence:transfer_custody', args=[evidence.id]), {
            'to_user': self.admin.id,
            'reason': 'Lab Analysis',
            'location': 'Forensic Lab'
        })
        
        # Accept custody as admin
        transfer = CustodyTransfer.objects.last()
        self.client.login(username="admin", password="password")
        self.client.post(reverse('evidence:accept_custody_transfer', args=[transfer.id]))
        
        evidence.refresh_from_db()
        self.assertEqual(evidence.current_custodian, self.admin)
        self.assertEqual(CustodyTransfer.objects.count(), 2)

    def test_unauthorized_user_cannot_access_evidence(self):
        # Create evidence as admin
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-002', description='Phone')
        
        self.client.login(username="officer_b", password="password")
        response = self.client.get(reverse('evidence:evidence_detail', args=[evidence.id]))
        self.assertEqual(response.status_code, 403)

    def test_evidence_approval_workflow(self):
        # Admin creates evidence
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-003', description='Tablet', current_custodian=self.officer_a)
        
        # Default status is PENDING_APPROVAL
        self.assertEqual(evidence.status, Evidence.Status.PENDING_APPROVAL)
        
        # Investigating officer tries to approve -> rejected with PermissionDenied (403)
        self.client.login(username="officer_a", password="password")
        response = self.client.post(reverse('evidence:approve_evidence', args=[evidence.id]), {
            'action': 'approve',
            'notes': 'Looks good'
        })
        self.assertEqual(response.status_code, 403)
        evidence.refresh_from_db()
        self.assertEqual(evidence.status, Evidence.Status.PENDING_APPROVAL)
        
        # Senior Officer/Admin tries to approve
        self.client.login(username="admin", password="password")
        response = self.client.post(reverse('evidence:approve_evidence', args=[evidence.id]), {
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
        response = self.client.post(reverse('evidence:transfer_custody', args=[evidence.id]), {
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
        response = self.client.post(reverse('evidence:accept_custody_transfer', args=[transfer.id]))
        
        evidence.refresh_from_db()
        transfer.refresh_from_db()
        
        self.assertEqual(transfer.status, CustodyTransfer.Status.ACCEPTED)
        self.assertEqual(evidence.current_custodian, self.officer_b)

    def test_cross_department_custody_transfer_to_judge(self):
        judge = User.objects.create_user(username="judge_verma", role=User.Role.COURT_USER, password="password")
        
        # Verify judge is NOT a member of case initially
        self.assertFalse(self.case.members.filter(user=judge).exists())
        
        # officer_a has custody of evidence
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-JUDGE-01', description='Encrypted Flash Drive', current_custodian=self.officer_a)
        
        # Before transfer, judge CANNOT view evidence
        self.client.login(username="judge_verma", password="password")
        response = self.client.get(reverse('evidence:evidence_detail', args=[evidence.id]))
        self.assertEqual(response.status_code, 403)
        
        # officer_a initiates transfer to judge
        self.client.login(username="officer_a", password="password")
        response = self.client.post(reverse('evidence:transfer_custody', args=[evidence.id]), {
            'to_user': judge.id,
            'reason': 'Court Evidence Presentation',
            'location': 'Courtroom 4B'
        })
        self.assertRedirects(response, reverse('evidence:evidence_detail', args=[evidence.id]))
        
        transfer = CustodyTransfer.objects.get(evidence=evidence, to_user=judge)
        self.assertEqual(transfer.status, CustodyTransfer.Status.PENDING)
        
        # Now judge CAN view evidence without receiving 403 Forbidden
        self.client.login(username="judge_verma", password="password")
        response = self.client.get(reverse('evidence:evidence_detail', args=[evidence.id]))
        self.assertEqual(response.status_code, 200)
        
        # Arbitrary third user (officer_b) CANNOT accept transfer meant for judge -> 403
        self.client.login(username="officer_b", password="password")
        unauthorized_accept = self.client.post(reverse('evidence:accept_custody_transfer', args=[transfer.id]))
        self.assertEqual(unauthorized_accept.status_code, 403)
        
        # Judge accepts transfer
        self.client.login(username="judge_verma", password="password")
        accept_response = self.client.post(reverse('evidence:accept_custody_transfer', args=[transfer.id]))
        self.assertRedirects(accept_response, reverse('evidence:evidence_detail', args=[evidence.id]))
        
        evidence.refresh_from_db()
        transfer.refresh_from_db()
        
        self.assertEqual(transfer.status, CustodyTransfer.Status.ACCEPTED)
        self.assertEqual(evidence.current_custodian, judge)
        
        # Judge can continue viewing evidence and was automatically added as case member
        self.assertTrue(self.case.members.filter(user=judge).exists())
        response = self.client.get(reverse('evidence:evidence_detail', args=[evidence.id]))
        self.assertEqual(response.status_code, 200)

    def test_reject_custody_transfer(self):
        evidence = Evidence.objects.create(case=self.case, evidence_number='EV-REJECT-01', description='Damaged Hard Disk', current_custodian=self.officer_a)
        
        # Transfer to officer_b
        self.client.login(username="officer_a", password="password")
        self.client.post(reverse('evidence:transfer_custody', args=[evidence.id]), {
            'to_user': self.officer_b.id,
            'reason': 'Forensic Extraction',
            'location': 'Lab 1'
        })
        transfer = CustodyTransfer.objects.get(evidence=evidence, to_user=self.officer_b)
        
        # Random third-party officer tries to reject -> 403
        random_user = User.objects.create_user(username="random_officer", role=User.Role.INVESTIGATING_OFFICER, password="password")
        self.client.login(username="random_officer", password="password")
        response = self.client.post(reverse('evidence:reject_custody_transfer', args=[transfer.id]))
        self.assertEqual(response.status_code, 403)
        
        # Intended recipient rejects transfer with reason
        self.client.login(username="officer_b", password="password")
        response = self.client.post(reverse('evidence:reject_custody_transfer', args=[transfer.id]), {
            'rejection_reason': 'Packaging seal broken on arrival'
        })
        self.assertRedirects(response, reverse('evidence:evidence_list'))
        
        transfer.refresh_from_db()
        evidence.refresh_from_db()
        self.assertEqual(transfer.status, CustodyTransfer.Status.REJECTED)
        self.assertEqual(transfer.rejection_reason, 'Packaging seal broken on arrival')
        # Custody remains with officer_a
        self.assertEqual(evidence.current_custodian, self.officer_a)
