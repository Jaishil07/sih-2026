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
        return f"{self.user.username} in {self.case.case_number} as {self.role}"


class PersonOfInterest(models.Model):
    class Role(models.TextChoices):
        SUSPECT = 'SUSPECT', 'Suspect'
        WITNESS = 'WITNESS', 'Witness'
        VICTIM = 'VICTIM', 'Victim'
        PERSON_OF_INTEREST = 'PERSON_OF_INTEREST', 'Person of Interest'

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='persons_of_interest')
    name = models.CharField(max_length=200)
    alias = models.CharField(max_length=100, blank=True)
    role_in_case = models.CharField(max_length=50, choices=Role.choices, default=Role.SUSPECT)
    identification_number = models.CharField(max_length=100, blank=True, help_text="Aadhaar, Passport, or Govt ID ref")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_role_in_case_display()})"

class CaseNote(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.author.username} on {self.case.case_number}"
