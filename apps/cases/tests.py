from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.cases.models import Case, CaseMember, PersonOfInterest

User = get_user_model()

class CaseTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.officer_a = User.objects.create_user(username="officer_a", role=User.Role.INVESTIGATING_OFFICER, password="password")
        self.officer_b = User.objects.create_user(username="officer_b", role=User.Role.INVESTIGATING_OFFICER, password="password")
        
        self.case = Case.objects.create(case_number="CR-TEST", title="Test Case", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.officer_a, role="Investigator")

    def test_add_person_of_interest(self):
        self.client.login(username="officer_a", password="password")
        
        response = self.client.post(reverse('add_person_of_interest', args=[self.case.id]), {
            'name': 'John Doe',
            'role_in_case': 'SUSPECT'
        })
        
        self.assertEqual(PersonOfInterest.objects.count(), 1)
        poi = PersonOfInterest.objects.first()
        self.assertEqual(poi.name, 'John Doe')
        self.assertEqual(poi.role_in_case, 'SUSPECT')

    def test_unauthorized_user_cannot_add_poi(self):
        self.client.login(username="officer_b", password="password")
        
        response = self.client.post(reverse('add_person_of_interest', args=[self.case.id]), {
            'name': 'Jane Doe',
            'role_in_case': 'WITNESS'
        })
        
        self.assertEqual(response.status_code, 403)
        self.assertEqual(PersonOfInterest.objects.count(), 0)

    def test_assign_multiple_officers(self):
        self.client.login(username="admin", password="password")
        
        # Assign officer_b to the case
        response = self.client.post(reverse('assign_member', args=[self.case.id]), {
            'user_id': self.officer_b.id,
            'role': 'Support'
        })
        
        self.assertEqual(CaseMember.objects.filter(case=self.case).count(), 2)
        
        # Now officer_b should be able to view the case detail
        self.client.login(username="officer_b", password="password")
        response = self.client.get(reverse('case_detail', args=[self.case.id]))
    def test_add_case_note(self):
        self.client.login(username="officer_a", password="password")
        
        response = self.client.post(reverse('add_case_note', args=[self.case.id]), {
            'content': 'Suspect was seen near the bank.'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.case.notes.count(), 1)
        self.assertEqual(self.case.notes.first().content, 'Suspect was seen near the bank.')
        
        # Verify both officers can read it (officer_b needs to be assigned first)
        CaseMember.objects.create(case=self.case, user=self.officer_b, role="Support")
        
        self.client.login(username="officer_b", password="password")
        response = self.client.get(reverse('case_detail', args=[self.case.id]))
        self.assertContains(response, 'Suspect was seen near the bank.')

class DelegationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN, password="password")
        self.senior = User.objects.create_user(username="senior", role=User.Role.SENIOR_OFFICER, password="password", department="Cyber")
        self.officer1 = User.objects.create_user(username="officer1", role=User.Role.INVESTIGATING_OFFICER, password="password", supervisor=self.senior, department="Cyber")
        self.officer2 = User.objects.create_user(username="officer2", role=User.Role.INVESTIGATING_OFFICER, password="password", department="Narcotics")
        
        self.case = Case.objects.create(case_number="CR-2", title="Delegation", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.senior, role="Supervisor")

    def test_senior_officer_assigns_subordinate(self):
        self.client.login(username="senior", password="password")
        response = self.client.post(reverse('assign_member', args=[self.case.id]), {
            'user_id': self.officer1.id,
            'role': 'Investigator'
        })
        self.assertEqual(CaseMember.objects.filter(case=self.case).count(), 2)
        
    def test_senior_officer_cannot_assign_non_subordinate(self):
        self.client.login(username="senior", password="password")
        response = self.client.post(reverse('assign_member', args=[self.case.id]), {
            'user_id': self.officer2.id,
            'role': 'Investigator'
        })
        self.assertEqual(response.status_code, 403)
        self.assertEqual(CaseMember.objects.filter(case=self.case).count(), 1)

    def test_investigating_officer_cannot_assign_or_close(self):
        CaseMember.objects.create(case=self.case, user=self.officer1, role="Investigator")
        self.client.login(username="officer1", password="password")
        
        # Try to assign
        response = self.client.post(reverse('assign_member', args=[self.case.id]), {
            'user_id': self.officer2.id,
            'role': 'Investigator'
        })
        self.assertEqual(response.status_code, 403)
        
        # Try to close
        response = self.client.post(reverse('case_close', args=[self.case.id]))
        self.assertEqual(response.status_code, 403)

    def test_closed_case_restrictions(self):
        # Admin closes case
        self.client.login(username="admin", password="password")
        self.client.post(reverse('case_close', args=[self.case.id]))
        
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, 'CLOSED')
        
        # Check UI hides upload buttons
        response = self.client.get(reverse('case_detail', args=[self.case.id]))
        self.assertContains(response, "CASE CLOSED")
        self.assertNotContains(response, "Upload Document")
