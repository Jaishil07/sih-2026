from django.urls import path
from apps.cases import views
from apps.cases.views import CaseListView, case_detail_view, add_person_of_interest_view, assign_member_view, add_case_note_view

urlpatterns = [
    path('', CaseListView.as_view(), name='case_list'),
    path('<int:pk>/', case_detail_view, name='case_detail'),
    path('<int:pk>/poi/add/', add_person_of_interest_view, name='add_person_of_interest'),
    path('<int:pk>/members/assign/', assign_member_view, name='assign_member'),
    path('<int:pk>/notes/add/', add_case_note_view, name='add_case_note'),
    path('new/', views.CaseCreateView.as_view(), name='case_create'),
    path('<int:pk>/close/', views.CaseCloseView.as_view(), name='case_close'),
    path('<int:pk>/reopen/', views.CaseReopenView.as_view(), name='case_reopen'),
]
