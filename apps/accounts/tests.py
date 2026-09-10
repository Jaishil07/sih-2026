from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.cases.models import Case, CaseMember
from apps.accounts.services import can_access_case

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            role=User.Role.INVESTIGATING_OFFICER,
            department="Cyber",
            employee_id="EMP-999"
        )
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, User.Role.INVESTIGATING_OFFICER)
        self.assertEqual(user.department, "Cyber")
        self.assertEqual(user.employee_id, "EMP-999")
        self.assertTrue(user.check_password("testpassword123"))


class AuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
        )

    def test_dashboard_redirects_if_not_logged_in(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "testpassword123"
        })
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_failure(self):
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct")


class AuthorizationServiceTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", role=User.Role.ADMIN)
        self.officer_a = User.objects.create_user(username="officer_a", role=User.Role.INVESTIGATING_OFFICER)
        self.officer_b = User.objects.create_user(username="officer_b", role=User.Role.INVESTIGATING_OFFICER)
        
        self.case = Case.objects.create(case_number="CR-TEST", title="Test Case", created_by=self.admin)
        CaseMember.objects.create(case=self.case, user=self.officer_a, role="Investigator")

    def test_can_access_case(self):
        # Admin can access
        self.assertTrue(can_access_case(self.admin, self.case))
        # Member can access
        self.assertTrue(can_access_case(self.officer_a, self.case))
        # Non-member cannot access
        self.assertFalse(can_access_case(self.officer_b, self.case))
