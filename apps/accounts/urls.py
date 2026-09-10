from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/deactivate/', views.UserDeactivateView.as_view(), name='user_deactivate'),
    path('users/<int:pk>/update-supervisor/', views.UserUpdateSupervisorView.as_view(), name='user_update_supervisor'),
    path('password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('mfa/verify/', views.MfaVerifyView.as_view(), name='mfa_verify'),
    path('mfa/setup/', views.MfaSetupView.as_view(), name='mfa_setup'),
]
