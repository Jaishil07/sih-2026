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

class UserAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="password", role=User.Role.ADMIN)
        self.officer = User.objects.create_user(username="officer", password="password", role=User.Role.INVESTIGATING_OFFICER)

    def test_admin_access_only(self):
        self.client.login(username="officer", password="password")
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 403)
        
        self.client.login(username="admin", password="password")
        response = self.client.get(reverse('user_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_user_by_admin(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(reverse('user_create'), {
            'username': 'new_user',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'role': User.Role.FORENSIC_OFFICER,
            'initial_password': 'strongpassword123'
        })
        self.assertRedirects(response, reverse('user_list'))
        
        new_user = User.objects.get(username="new_user")
        self.assertTrue(new_user.check_password("strongpassword123"))
        
        # Check audit log
        from apps.audit.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action='USER_CREATED', resource_type='User', resource_id=str(new_user.id)).exists())

    def test_deactivate_user(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(reverse('user_deactivate', args=[self.officer.id]))
        self.assertRedirects(response, reverse('user_list'))
        
        self.officer.refresh_from_db()
        self.assertFalse(self.officer.is_active)
        
        # Test login fails
        login_success = self.client.login(username="officer", password="password")
        self.assertFalse(login_success)

class PasswordChangeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test_pass", password="oldpassword123")
        
    def test_password_change(self):
        self.client.login(username="test_pass", password="oldpassword123")
        response = self.client.post(reverse('password_change'), {
            'old_password': 'oldpassword123',
            'new_password1': 'NewStrongPass!123',
            'new_password2': 'NewStrongPass!123'
        })
        self.assertRedirects(response, reverse('dashboard'))
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass!123'))
        
    def test_invalid_old_password(self):
        self.client.login(username="test_pass", password="oldpassword123")
        response = self.client.post(reverse('password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'NewStrongPass!123',
            'new_password2': 'NewStrongPass!123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your old password was entered incorrectly')

class MfaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mfauser",
            password="testpassword123",
        )
        import pyotp
        self.mfa_secret = pyotp.random_base32()
        self.user.mfa_enabled = True
        self.user.mfa_secret = self.mfa_secret
        self.user.save()
        
    def test_mfa_login_redirect(self):
        response = self.client.post(reverse("login"), {
            "username": "mfauser",
            "password": "testpassword123"
        })
        self.assertRedirects(response, reverse("mfa_verify"))
        self.assertEqual(self.client.session.get('mfa_pre_verify_user_pk'), self.user.pk)
        
    def test_mfa_verify_success(self):
        session = self.client.session
        session['mfa_pre_verify_user_pk'] = self.user.pk
        session.save()
        
        import pyotp
        totp = pyotp.totp.TOTP(self.mfa_secret)
        token = totp.now()
        
        response = self.client.post(reverse("mfa_verify"), {
            "token": token
        })
        self.assertRedirects(response, reverse("dashboard"))
        
        # Check audit log
        from apps.audit.models import AuditLog
        self.assertTrue(AuditLog.objects.filter(action='MFA_LOGIN_SUCCESS', resource_id=str(self.user.id)).exists())
        
    def test_mfa_verify_invalid_token(self):
        session = self.client.session
        session['mfa_pre_verify_user_pk'] = self.user.pk
        session.save()
        
        response = self.client.post(reverse("mfa_verify"), {
            "token": "000000"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid or expired Authenticator code")
