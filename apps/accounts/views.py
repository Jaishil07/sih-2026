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
        context["cases_assigned"] = user.casemember_set.count() if hasattr(user, "casemember_set") else 0
        context["available_documents"] = 0 # To be implemented
        context["tracked_evidence"] = 0 # To be implemented
        
        return context
