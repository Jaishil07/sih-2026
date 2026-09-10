import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.contrib import messages
from django.views.generic import ListView
from django.views.decorators.clickjacking import xframe_options_sameorigin

from apps.cases.models import Case
from apps.documents.models import Document, DocumentVersion
from apps.documents.forms import DocumentUploadForm, DocumentVersionUploadForm
from apps.documents.services import create_document_version, verify_document_version_integrity
from apps.accounts.services import can_access_case, can_view_document, can_upload_document, can_delete_document
from apps.audit.services import log_audit_event


class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.ADMIN:
            return Document.objects.exclude(status='ARCHIVED').order_by('-created_at')
        return Document.objects.filter(case__members__user=user).exclude(status='ARCHIVED').distinct().order_by('-created_at')


@login_required
def document_upload_view(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    if not can_upload_document(request.user, case):
        raise PermissionDenied
        
    if case.status == 'CLOSED':
        messages.error(request, "Cannot upload documents to a closed case.")
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
                
                # Trigger AI processing
                from apps.ai_assistant.services import process_document_with_ai
                process_document_with_ai(document, request.user)
                
                log_audit_event(request.user, 'DOCUMENT_UPLOADED', 'Document', document.id)
                messages.success(request, f"Document '{document.title}' uploaded and AI analysis initiated.")
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

    # Run AI Analysis on-demand
    if 'run_ai' in request.GET:
        from apps.ai_assistant.services import process_document_with_ai
        process_document_with_ai(document, request.user)
        messages.success(request, "AI Analysis completed.")
        return redirect('document_detail', pk=document.id)

    ai_result = document.ai_results.order_by('-created_at').first()

    # Version Upload form
    if request.method == 'POST':
        if document.case.status == 'CLOSED':
            messages.error(request, "Cannot upload new versions to a closed case.")
            raise PermissionDenied
            
        form = DocumentVersionUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            change_reason = form.cleaned_data['change_reason']
            try:
                version = create_document_version(document, uploaded_file, request.user, change_reason)
                
                # Trigger AI processing for new version
                from apps.ai_assistant.services import process_document_with_ai
                process_document_with_ai(document, request.user)
                
                log_audit_event(request.user, 'VERSION_CREATED', 'Document', document.id)
                messages.success(request, f"New version (v{version.version_number}) uploaded and AI analysis updated.")
                return redirect('document_detail', pk=document.id)
            except Exception as e:
                messages.error(request, f"Failed to upload new version: {e}")
    else:
        form = DocumentVersionUploadForm()

    # Read the file extension and determine file_type
    latest_version = current_version
    ext = os.path.splitext(getattr(latest_version, 'original_filename', None) or (os.path.basename(latest_version.file.name) if latest_version and latest_version.file else ''))[1].lower() if latest_version else ''
    file_ext = ext
    
    if ext == '.pdf':
        file_type = 'pdf'
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']:
        file_type = 'image'
    elif ext in ['.txt', '.log', '.json', '.csv']:
        file_type = 'text'
    else:
        file_type = 'other'

    preview_text_content = ''
    if file_type == 'text' and latest_version and latest_version.file:
        try:
            if os.path.exists(latest_version.file.path):
                with open(latest_version.file.path, 'r', encoding='utf-8', errors='replace') as f:
                    preview_text_content = f.read(50 * 1024)
        except Exception:
            preview_text_content = "Unable to read text preview."

    # Look up blockchain anchor block
    blockchain_block = None
    if current_version:
        from apps.blockchain.models import Block
        for b in Block.objects.order_by('-index')[:50]:
            if any(
                isinstance(tx, dict) and (
                    tx.get('sha256_hash') == current_version.sha256_hash or
                    (tx.get('doc_id') == document.id and tx.get('version') == current_version.version_number)
                )
                for tx in b.transactions
            ):
                blockchain_block = b
                break

    return render(request, 'documents/document_detail.html', {
        'document': document,
        'current_version': current_version,
        'versions': versions,
        'integrity_status': integrity_status,
        'form': form,
        'ai_result': ai_result,
        'file_type': file_type,
        'file_ext': file_ext,
        'preview_text_content': preview_text_content,
        'blockchain_block': blockchain_block,
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


@login_required
def document_delete_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    if not can_delete_document(request.user, document):
        raise PermissionDenied
        
    if request.method == 'POST':
        document.status = 'ARCHIVED'
        document.save()
        log_audit_event(request.user, 'DOCUMENT_ARCHIVED', 'Document', document.id)
        messages.success(request, f"Document '{document.title}' has been archived.")
        return redirect('case_detail', pk=document.case.id)
        
    # GET method is not supported for delete/archive to prevent accidental/CSRF deletions.
    return redirect('document_detail', pk=document.id)

@xframe_options_sameorigin
@login_required
def document_preview_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if not can_view_document(request.user, document):
        raise PermissionDenied
        
    version = document.versions.order_by('-version_number').first()
    if not version or not version.file:
        raise Http404("Document file missing.")

    # In-memory decryption if enabled, or read bytes
    try:
        file_path = version.file.path
        if not os.path.exists(file_path):
            raise Http404("Document file missing.")
    except Exception:
        raise Http404("Document file missing.")

    original_filename = getattr(version, 'original_filename', None) or os.path.basename(version.file.name)
    ext = os.path.splitext(original_filename)[1].lower()
    
    content_types = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.txt': 'text/plain; charset=utf-8',
        '.log': 'text/plain; charset=utf-8',
        '.json': 'application/json',
        '.csv': 'text/plain; charset=utf-8',
    }
    content_type = content_types.get(ext, 'application/octet-stream')
    
    log_audit_event(request.user, 'DOCUMENT_PREVIEWED', 'DocumentVersion', version.id)
    
    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{original_filename}"'
    return response

@login_required
def document_sign_view(request, pk):
    document = get_object_or_404(Document, pk=pk)
    
    # Check if authorized to sign. We reuse can_upload_document since it covers Admin, Senior, and assigned investigators.
    if not can_upload_document(request.user, document.case):
        raise PermissionDenied
        
    if request.method == 'POST':
        version = document.versions.order_by('-version_number').first()
        if not version:
            messages.error(request, "No versions to sign.")
            return redirect('document_detail', pk=document.id)
            
        try:
            from apps.documents.services import sign_document_version
            doc_sig = sign_document_version(version, request.user)
            messages.success(request, f"Document digitally signed and locked! Cert ID: {doc_sig.certificate_id}")
        except PermissionDenied as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Failed to sign document: {str(e)}")
            
    return redirect('document_detail', pk=document.id)
