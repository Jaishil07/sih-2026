from django.urls import path
from . import views

urlpatterns = [
    path('', views.AuditListView.as_view(), name='audit_list'),
    path('verify/', views.verify_audit_chain_view, name='verify_audit_chain'),
]
