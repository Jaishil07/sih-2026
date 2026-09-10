from django.db import models
from apps.documents.models import Document

class DocumentText(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='extracted_text')
    raw_text = models.TextField()
    extraction_method = models.CharField(max_length=50, default='PYPDF_TEXT')
    extracted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Text for {self.document.title}"

class AIResult(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='ai_results')
    summary = models.TextField(blank=True)
    key_findings = models.JSONField(default=list)
    entities = models.JSONField(default=dict)
    suggested_type = models.CharField(max_length=50, blank=True)
    suggested_classification = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"AI Result for {self.document.title}"
