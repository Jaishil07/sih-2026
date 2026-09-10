from django.conf import settings
from django.db import models

from apps.cases.models import Case


class Document(models.Model):
    class DocumentType(models.TextChoices):
        FIR = 'FIR', 'First Information Report (FIR)'
        FORENSIC_REPORT = 'FORENSIC_REPORT', 'Forensic Analysis Report'
        WITNESS_STATEMENT = 'WITNESS_STATEMENT', 'Witness Statement'
        CHARGE_SHEET = 'CHARGE_SHEET', 'Charge Sheet'
        COURT_FILING = 'COURT_FILING', 'Court Filing'
        LEGAL_NOTICE = 'LEGAL_NOTICE', 'Legal Notice'
        JUDGMENT = 'JUDGMENT', 'Judgment / Court Order'
        OTHER = 'OTHER', 'Other Supporting Document'

    class Classification(models.TextChoices):
        INTERNAL = 'INTERNAL', 'Internal / Restricted'
        CONFIDENTIAL = 'CONFIDENTIAL', 'Confidential'
        HIGHLY_CONFIDENTIAL = 'HIGHLY_CONFIDENTIAL', 'Highly Confidential / Secret'
        EVIDENCE = 'EVIDENCE', 'Evidentiary Record'

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100, choices=DocumentType.choices, default=DocumentType.OTHER)
    classification = models.CharField(max_length=50, choices=Classification.choices, default=Classification.INTERNAL)
    status = models.CharField(max_length=50, default="ACTIVE")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="versions"
    )
    version_number = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to="documents/%Y/%m/")
    sha256_hash = models.CharField(max_length=64, blank=True)
    change_reason = models.CharField(max_length=255, blank=True)
    is_signed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"
