from django import forms
from apps.documents.models import Document

class DocumentUploadForm(forms.ModelForm):
    file = forms.FileField(required=True)
    change_reason = forms.CharField(max_length=255, required=False, help_text="Reason for uploading (optional for v1).")

    class Meta:
        model = Document
        fields = ['title', 'document_type', 'classification']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'classification': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        self.fields['change_reason'].widget = forms.TextInput(attrs={'class': 'form-control'})

class DocumentVersionUploadForm(forms.Form):
    file = forms.FileField(required=True)
    change_reason = forms.CharField(max_length=255, required=True, help_text="Mandatory reason for new version.")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'class': 'form-control'})
        self.fields['change_reason'].widget = forms.TextInput(attrs={'class': 'form-control'})
