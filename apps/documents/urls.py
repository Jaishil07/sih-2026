from django.urls import path
from . import views

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='document_list'),
    path('case/<int:case_id>/upload/', views.document_upload_view, name='document_upload'),
    path('<int:pk>/', views.document_detail_view, name='document_detail'),
    path('<int:pk>/delete/', views.document_delete_view, name='document_delete'),
    path('<int:pk>/preview/', views.document_preview_view, name='document_preview'),
    path('<int:pk>/sign/', views.document_sign_view, name='document_sign'),
    path('version/<int:version_id>/download/', views.document_download_view, name='document_download'),
]
