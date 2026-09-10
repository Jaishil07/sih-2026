from django.urls import path
from apps.evidence.views import (
    EvidenceListView, evidence_detail_view, evidence_create_view, approve_evidence_view,
    accept_custody_transfer_view, reject_custody_transfer_view
)

urlpatterns = [
    path('', EvidenceListView.as_view(), name='evidence_list'),
    path('case/<int:case_id>/add/', evidence_create_view, name='evidence_create'),
    path('<int:evidence_id>/', evidence_detail_view, name='evidence_detail'),
    path('<int:evidence_id>/approve/', approve_evidence_view, name='approve_evidence'),
    path('transfer/<int:transfer_id>/accept/', accept_custody_transfer_view, name='accept_custody_transfer'),
    path('transfer/<int:transfer_id>/reject/', reject_custody_transfer_view, name='reject_custody_transfer'),
]
