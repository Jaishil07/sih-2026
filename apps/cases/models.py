from django.conf import settings
from django.db import models


class Case(models.Model):
    case_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="OPEN")
    classification = models.CharField(max_length=50, default="INTERNAL")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.case_number} - {self.title}"


class CaseMember(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("case", "user")

    def __str__(self):
        return f"{self.user.username} in {self.case.case_number} ({self.role})"
