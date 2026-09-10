from django.contrib import admin
from django.urls import path, include

from apps.accounts import views as account_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", account_views.CustomLoginView.as_view(), name="login"),
    path("accounts/logout/", account_views.CustomLogoutView.as_view(), name="logout"),
    path("cases/", include("apps.cases.urls")),
    path("documents/", include("apps.documents.urls")),
    path("evidence/", include(("apps.evidence.urls", "evidence"), namespace="evidence")),
    path("evidence/", include("apps.evidence.urls")),
    path("audit/", include("apps.audit.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.ai_assistant.urls")),
    path("", account_views.DashboardView.as_view(), name="dashboard"),
]
