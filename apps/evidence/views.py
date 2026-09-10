from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.cases.models import Case
from apps.evidence.models import Evidence, CustodyTransfer
from apps.accounts.services import can_access_case, can_view_evidence
from apps.audit.services import log_audit_event

User = get_user_model()

class EvidenceListView(LoginRequiredMixin, ListView):
    model = Evidence
    template_name = "evidence/evidence_list.html"
    context_object_name = "evidence_items"

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.ADMIN:
            return Evidence.objects.all().order_by('-created_at')
        return Evidence.objects.filter(case__members__user=user).distinct().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_transfers"] = CustodyTransfer.objects.filter(
            to_user=self.request.user,
            status=CustodyTransfer.Status.PENDING
        ).order_by('-timestamp')
        return context

@login_required
def evidence_create_view(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    if not can_access_case(request.user, case):
        raise PermissionDenied
        
    if request.method == 'POST':
        evidence_number = request.POST.get('evidence_number')
        description = request.POST.get('description')
        
        evidence = Evidence.objects.create(
            case=case,
            evidence_number=evidence_number,
            description=description,
            current_custodian=request.user
        )
        
        # Initial transfer log
        CustodyTransfer.objects.create(
            evidence=evidence,
            from_user=None,
            to_user=request.user,
            reason="Initial Collection",
            location="Field",
            status=CustodyTransfer.Status.ACCEPTED,
            accepted_at=timezone.now()
        )
        
        log_audit_event(request.user, 'EVIDENCE_CREATED', 'Evidence', evidence.id)
        messages.success(request, f"Evidence {evidence_number} registered.")
        return redirect('evidence_detail', evidence_id=evidence.id)

    return render(request, 'evidence/evidence_create.html', {'case': case})

@login_required
def evidence_detail_view(request, evidence_id):
    evidence = get_object_or_404(Evidence, id=evidence_id)
    if not can_view_evidence(request.user, evidence):
        raise PermissionDenied
        
    if request.method == 'POST':
        # Handling Custody Transfer form
        to_user_id = request.POST.get('to_user')
        reason = request.POST.get('reason')
        location = request.POST.get('location')
        
        to_user = get_object_or_404(User, id=to_user_id)
        
        transfer = CustodyTransfer.objects.create(
            evidence=evidence,
            from_user=evidence.current_custodian,
            to_user=to_user,
            reason=reason,
            location=location,
            status=CustodyTransfer.Status.PENDING
        )
        # Note: We DO NOT update evidence.current_custodian here! It stays with sender.
        
        log_audit_event(request.user, 'CUSTODY_TRANSFER_INITIATED', 'Evidence', evidence.id)
        messages.success(request, f"Custody transfer initiated to {to_user.username}. Awaiting their acceptance.")
        return redirect('evidence_detail', evidence_id=evidence.id)
        
    users = User.objects.all()
    transfers = evidence.transfers.all().order_by('-timestamp')
    
    return render(request, 'evidence/evidence_detail.html', {
        'evidence': evidence,
        'transfers': transfers,
        'users': users
    })

@login_required
def approve_evidence_view(request, evidence_id):
    if request.method != 'POST':
        return redirect('evidence_detail', evidence_id=evidence_id)
        
    evidence = get_object_or_404(Evidence, id=evidence_id)
    
    # Check permissions: ADMIN, SENIOR_OFFICER, or Case Lead. Simplified: ADMIN or SENIOR_OFFICER.
    if request.user.role not in [request.user.Role.ADMIN, request.user.Role.SENIOR_OFFICER]:
        messages.error(request, "Permission denied. Only Admins or Senior Officers can approve evidence.")
        return redirect('evidence_detail', evidence_id=evidence.id)
        
    action = request.POST.get('action') # 'approve' or 'reject'
    notes = request.POST.get('notes', '')
    
    if action == 'approve':
        evidence.status = Evidence.Status.APPROVED
        audit_action = 'EVIDENCE_APPROVED'
        messages.success(request, f"Evidence {evidence.evidence_number} approved.")
    elif action == 'reject':
        evidence.status = Evidence.Status.REJECTED
        audit_action = 'EVIDENCE_REJECTED'
        messages.success(request, f"Evidence {evidence.evidence_number} rejected.")
    else:
        return redirect('evidence_detail', evidence_id=evidence.id)
        
    evidence.approved_by = request.user
    evidence.approved_at = timezone.now()
    evidence.approval_notes = notes
    evidence.save()
    
    log_audit_event(request.user, audit_action, 'Evidence', evidence.id)
    return redirect('evidence_detail', evidence_id=evidence.id)

@login_required
def accept_custody_transfer_view(request, transfer_id):
    if request.method != 'POST':
        return redirect('evidence_list')
        
    transfer = get_object_or_404(CustodyTransfer, id=transfer_id)
    if request.user != transfer.to_user:
        messages.error(request, "Permission denied. You are not the recipient of this transfer.")
        return redirect('evidence_list')
        
    if transfer.status != CustodyTransfer.Status.PENDING:
        messages.error(request, "This transfer is no longer pending.")
        return redirect('evidence_detail', evidence_id=transfer.evidence.id)
        
    transfer.status = CustodyTransfer.Status.ACCEPTED
    transfer.accepted_at = timezone.now()
    transfer.save()
    
    evidence = transfer.evidence
    evidence.current_custodian = request.user
    evidence.save()
    
    log_audit_event(request.user, 'CUSTODY_TRANSFER_ACCEPTED', 'Evidence', evidence.id)
    messages.success(request, f"You have accepted custody of Evidence {evidence.evidence_number}.")
    return redirect('evidence_detail', evidence_id=evidence.id)

@login_required
def reject_custody_transfer_view(request, transfer_id):
    if request.method != 'POST':
        return redirect('evidence_list')
        
    transfer = get_object_or_404(CustodyTransfer, id=transfer_id)
    if request.user != transfer.to_user:
        messages.error(request, "Permission denied. You are not the recipient of this transfer.")
        return redirect('evidence_list')
        
    if transfer.status != CustodyTransfer.Status.PENDING:
        messages.error(request, "This transfer is no longer pending.")
        return redirect('evidence_detail', evidence_id=transfer.evidence.id)
        
    reason = request.POST.get('rejection_reason', 'No reason provided.')
    transfer.status = CustodyTransfer.Status.REJECTED
    transfer.rejection_reason = reason
    transfer.save()
    
    log_audit_event(request.user, 'CUSTODY_TRANSFER_REJECTED', 'Evidence', transfer.evidence.id)
    messages.warning(request, f"You rejected the custody transfer of Evidence {transfer.evidence.evidence_number}.")
    return redirect('evidence_detail', evidence_id=transfer.evidence.id)
