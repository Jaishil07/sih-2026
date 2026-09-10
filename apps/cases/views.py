from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView
from django.core.exceptions import PermissionDenied
from apps.cases.models import Case
from apps.accounts.services import can_access_case

class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = "cases/case_list.html"
    context_object_name = "cases"

    def get_queryset(self):
        if self.request.user.role == self.request.user.Role.ADMIN:
            return Case.objects.all()
        return Case.objects.filter(members__user=self.request.user)

class CaseDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Case
    template_name = "cases/case_detail.html"
    context_object_name = "case"

    def test_func(self):
        case = self.get_object()
        return can_access_case(self.request.user, case)
