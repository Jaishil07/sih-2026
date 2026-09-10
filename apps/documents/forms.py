from django import forms
from apps.documents.models import Document

class DocumentUploadForm(forms.ModelForm):
    file = forms.FileField(required=True)
    change_reason = forms.CharField(max_length=255, required=False, help_text="Reason for uploading (optional for v1).")

    class Meta:
        model = Document
        fields = ['title', 'document_type', 'classification']

class DocumentVersionUploadForm(forms.Form):
    file = forms.FileField(required=True)
    change_reason = forms.CharField(max_length=255, required=True, help_text="Mandatory reason for new version.")
