from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"


class CustomLogoutView(LogoutView):
    next_page = "login"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add basic metrics
        from apps.cases.models import Case
        from apps.documents.models import Document
        from apps.evidence.models import Evidence
        from apps.audit.models import AuditLog
        
        if user.role == user.Role.ADMIN:
            cases = Case.objects.all()
        else:
            cases = Case.objects.filter(members__user=user)
            
        context["cases_assigned"] = cases.count()
        context["available_documents"] = Document.objects.filter(case__in=cases).distinct().count()
        context["tracked_evidence"] = Evidence.objects.filter(case__in=cases).distinct().count()
        
        # Recent Activity
        if user.role == user.Role.ADMIN:
            context["recent_activity"] = AuditLog.objects.all().order_by('-timestamp')[:5]
        else:
            # For non-admins, we'd filter audit logs based on accessible resources.
            # Simplified: just show logs triggered by them for now, or logs related to their cases.
            context["recent_activity"] = AuditLog.objects.filter(actor=user).order_by('-timestamp')[:5]
            
        return context
