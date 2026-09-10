from django.conf import settings
from django.db import models

from apps.cases.models import Case


class Evidence(models.Model):
    case = models.ForeignKey(
        Case, on_delete=models.CASCADE, related_name="evidence_items"
    )
    evidence_number = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    current_custodian = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    class Status(models.TextChoices):
        PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_APPROVAL)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_evidence'
    )
    approval_notes = models.TextField(blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.evidence_number


class CustodyTransfer(models.Model):
    evidence = models.ForeignKey(
        Evidence, on_delete=models.CASCADE, related_name="transfers"
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfers_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transfers_received",
    )
    reason = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evidence.evidence_number}: {self.from_user} -> {self.to_user}"
