from django.urls import path
from . import views

urlpatterns = [
    path('', views.CaseListView.as_view(), name='case_list'),
    path('<int:pk>/', views.CaseDetailView.as_view(), name='case_detail'),
]
