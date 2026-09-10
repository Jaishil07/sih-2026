from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.audit.models import AuditLog
from apps.audit.services import verify_audit_chain

class AuditListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = "audit/audit_list.html"
    context_object_name = "logs"

    def get_queryset(self):
        user = self.request.user
        base_qs = AuditLog.objects.all().order_by('-id')
        
        if user.role in [user.Role.ADMIN, user.Role.AUDITOR]:
            return base_qs[:100]
            
        subordinates = user.subordinates.all()
        if subordinates.exists():
            actors = [user] + list(subordinates)
            return base_qs.filter(actor__in=actors)[:100]
            
        from apps.cases.models import Case
        from apps.evidence.models import Evidence
        from django.db.models import Q
        
        user_cases = Case.objects.filter(members__user=user).values_list('id', flat=True)
        case_evidence = Evidence.objects.filter(case__in=user_cases).values_list('id', flat=True)
        
        return base_qs.filter(
            Q(actor=user) | 
            Q(resource_type='Case', resource_id__in=user_cases) |
            Q(resource_type='Evidence', resource_id__in=case_evidence)
        )[:100]


@login_required
def verify_audit_chain_view(request):
    if request.user.role != request.user.Role.ADMIN:
        messages.error(request, "Permission denied. Only ADMIN can verify the global audit chain.")
        return redirect('audit_list')
        
    is_valid, broken_id = verify_audit_chain()
    if is_valid:
        messages.success(request, "✓ Audit Chain Valid: Cryptographic integrity confirmed.")
    else:
        messages.error(request, f"⚠ TAMPER DETECTED: Audit Chain Integrity Failure at Log ID {broken_id}")
    return redirect('audit_list')
