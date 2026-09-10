from django.urls import path
from . import views

urlpatterns = [
    path('', views.CaseListView.as_view(), name='case_list'),
    path('<int:pk>/', views.case_detail_view, name='case_detail'),
    path('<int:pk>/add_poi/', views.add_person_of_interest_view, name='add_person_of_interest'),
    path('<int:pk>/assign_member/', views.assign_member_view, name='assign_member'),
]
