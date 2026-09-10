from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.contrib import messages
from django.views.generic import ListView

from apps.cases.models import Case
from apps.documents.models import Document, DocumentVersion
from apps.documents.forms import DocumentUploadForm, DocumentVersionUploadForm
from apps.documents.services import create_document_version, verify_document_version_integrity
from apps.accounts.services import can_access_case, can_view_document
from apps.audit.services import log_audit_event


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.ADMIN:
            return Document.objects.all().order_by('-created_at')
        return Document.objects.filter(case__members__user=user).distinct().order_by('-created_at')


@login_required
def document_upload_view(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    if not can_access_case(request.user, case):
        raise PermissionDenied

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.case = case
            document.created_by = request.user
            document.save()

            uploaded_file = form.cleaned_data['file']
            change_reason = form.cleaned_data.get('change_reason', 'Initial upload')
            
            try:
                version = create_document_version(document, uploaded_file, request.user, change_reason)
                log_audit_event(request.user, 'DOCUMENT_UPLOADED', 'Document', document.id)
                messages.success(request, f"Document '{document.title}' uploaded successfully.")
                return redirect('case_detail', pk=case.id)
            except Exception as e:
                document.delete() # Rollback document if version creation fails
                form.add_error('file', str(e))
    else:
        form = DocumentUploadForm()

    return render(request, 'documents/document_upload.html', {'form': form, 'case': case})


@login_required
def document_detail_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if not can_view_document(request.user, document):
        raise PermissionDenied

    versions = document.versions.all().order_by('-version_number')
    current_version = versions.first()

    integrity_status = None
    if 'verify_integrity' in request.GET and current_version:
        integrity_status = verify_document_version_integrity(current_version)
        if integrity_status:
            log_audit_event(request.user, 'INTEGRITY_VERIFIED', 'DocumentVersion', current_version.id)
            messages.success(request, "File integrity verified successfully.")
        else:
            log_audit_event(request.user, 'INTEGRITY_FAILED', 'DocumentVersion', current_version.id)
            messages.error(request, "TAMPER DETECTED: File integrity check failed!")

    # Version Upload form
    if request.method == 'POST':
        form = DocumentVersionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            change_reason = form.cleaned_data['change_reason']
            try:
                version = create_document_version(document, uploaded_file, request.user, change_reason)
                log_audit_event(request.user, 'VERSION_CREATED', 'Document', document.id)
                messages.success(request, f"New version (v{version.version_number}) uploaded.")
                return redirect('document_detail', pk=document.id)
            except Exception as e:
                messages.error(request, f"Failed to upload new version: {e}")
    else:
        form = DocumentVersionUploadForm()

    return render(request, 'documents/document_detail.html', {
        'document': document,
        'current_version': current_version,
        'versions': versions,
        'integrity_status': integrity_status,
        'form': form
    })


@login_required
def document_download_view(request, version_id):
    version = get_object_or_404(DocumentVersion, pk=version_id)
    if not can_view_document(request.user, version.document):
        raise PermissionDenied

    if not version.file or not version.file.storage.exists(version.file.name):
        raise Http404("File not found.")

    log_audit_event(request.user, 'DOCUMENT_DOWNLOADED', 'DocumentVersion', version.id)
    
    response = FileResponse(version.file.open('rb'))
    response['Content-Disposition'] = f'attachment; filename="{version.file.name.split("/")[-1]}"'
    return response
