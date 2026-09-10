from django.urls import path
from . import views

urlpatterns = [
    path('', views.EvidenceListView.as_view(), name='evidence_list'),
    path('new/<int:case_id>/', views.evidence_create_view, name='evidence_create'),
    path('<int:evidence_id>/', views.evidence_detail_view, name='evidence_detail'),
    path('<int:evidence_id>/approve/', views.approve_evidence_view, name='approve_evidence'),
]
