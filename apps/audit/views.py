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
        # Display latest 100 for performance
        return AuditLog.objects.all().order_by('-id')[:100]


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
