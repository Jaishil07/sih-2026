from django.contrib.auth.models import AbstractUser
from django.db import models
import pyotp


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    Adds employee_id, role, designation, and department as required by
    docs/DATABASE.md and docs/PROJECT_SPEC.md.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        SENIOR_OFFICER = "SENIOR_OFFICER", "Senior Officer"
        INVESTIGATING_OFFICER = "INVESTIGATING_OFFICER", "Investigating Officer"
        FORENSIC_OFFICER = "FORENSIC_OFFICER", "Forensic Officer"
        PROSECUTOR = "PROSECUTOR", "Prosecutor"
        COURT_USER = "COURT_USER", "Court User"
        AUDITOR = "AUDITOR", "Auditor"

    employee_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique employee identifier",
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.INVESTIGATING_OFFICER,
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )
    designation = models.CharField(
        max_length=100,
        blank=True,
    )
    supervisor = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='subordinates'
    )
    
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=64, blank=True, null=True)

    def generate_mfa_secret(self):
        self.mfa_secret = pyotp.random_base32()
        self.save()

    def get_totp_uri(self):
        if not self.mfa_secret:
            return None
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.username, 
            issuer_name="Suraksha Docs"
        )

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
