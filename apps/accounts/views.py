from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.contrib.auth import login as auth_login
import pyotp
import qrcode
from io import BytesIO
import base64

class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    
    def form_valid(self, form):
        user = form.get_user()
        if user.mfa_enabled:
            self.request.session['mfa_pre_verify_user_pk'] = user.pk
            redirect_to = self.request.POST.get('next', '')
            if redirect_to:
                self.request.session['mfa_next'] = redirect_to
            return redirect('mfa_verify')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    next_page = "login"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Add basic metrics
        from apps.cases.models import Case
        from apps.documents.models import Document
        from apps.evidence.models import Evidence
        from apps.audit.models import AuditLog
        
        if user.role == user.Role.ADMIN:
            cases = Case.objects.all()
        else:
            cases = Case.objects.filter(members__user=user)
            
        context["cases_assigned"] = cases.count()
        context["available_documents"] = Document.objects.filter(case__in=cases).distinct().count()
        context["tracked_evidence"] = Evidence.objects.filter(case__in=cases).distinct().count()
        
        # Recent Activity
        if user.role == user.Role.ADMIN:
            context["recent_activity"] = AuditLog.objects.all().order_by('-timestamp')[:5]
        else:
            # For non-admins, we'd filter audit logs based on accessible resources.
            # Simplified: just show logs triggered by them for now, or logs related to their cases.
            context["recent_activity"] = AuditLog.objects.filter(actor=user).order_by('-timestamp')[:5]
            
        # Pending Custody Transfers
        from apps.evidence.models import CustodyTransfer
        context["pending_transfers"] = CustodyTransfer.objects.filter(
            to_user=user, 
            status=CustodyTransfer.Status.PENDING
        ).order_by('-timestamp')
            
        return context

class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != request.user.Role.ADMIN:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

from django.views.generic import ListView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views import View
from apps.audit.services import log_audit_event
from .forms import UserCreationForm, SupervisorUpdateForm
from django.contrib.auth.views import PasswordChangeView

User = get_user_model()

class MfaVerifyView(View):
    template_name = "accounts/mfa_verify.html"

    def get(self, request, *args, **kwargs):
        if 'mfa_pre_verify_user_pk' not in request.session:
            return redirect('login')
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        user_pk = request.session.get('mfa_pre_verify_user_pk')
        if not user_pk:
            return redirect('login')
            
        user = get_object_or_404(User, pk=user_pk)
        token = request.POST.get('token', '')
        
        totp = pyotp.totp.TOTP(user.mfa_secret)
        if totp.verify(token):
            auth_login(request, user)
            del request.session['mfa_pre_verify_user_pk']
            log_audit_event(user, 'MFA_LOGIN_SUCCESS', 'User', user.id)
            
            next_url = request.session.pop('mfa_next', None)
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid or expired Authenticator code.")
            return render(request, self.template_name)

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if not user.mfa_enabled and not user.mfa_secret:
            user.generate_mfa_secret()
            
        if user.mfa_secret:
            uri = user.get_totp_uri()
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer)
            qr_b64 = base64.b64encode(buffer.getvalue()).decode()
            context['qr_data_uri'] = f"data:image/png;base64,{qr_b64}"
            
        return context

class MfaSetupView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        action = request.POST.get('action')
        
        if action == 'disable':
            user.mfa_enabled = False
            user.mfa_secret = ''
            user.save()
            log_audit_event(user, 'MFA_DISABLED', 'User', user.id)
            messages.success(request, "Two-Factor Authentication has been disabled.")
            return redirect('profile')
            
        token = request.POST.get('token', '')
        totp = pyotp.totp.TOTP(user.mfa_secret)
        if totp.verify(token):
            user.mfa_enabled = True
            user.save()
            log_audit_event(user, 'MFA_ENABLED', 'User', user.id)
            messages.success(request, "Two-Factor Authentication has been successfully enabled.")
        else:
            messages.error(request, "Invalid Authenticator code. Please try again.")
        return redirect('profile')

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_manage.html"
    context_object_name = "users"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_form'] = UserCreationForm()
        context['supervisor_form'] = SupervisorUpdateForm()
        return context

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "accounts/user_manage.html"
    success_url = reverse_lazy('user_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'USER_CREATED', 'User', self.object.id)
        messages.success(self.request, f"User {self.object.username} created successfully.")
        return response
        
    def form_invalid(self, form):
        messages.error(self.request, f"Failed to create user. Errors: {form.errors}")
        return redirect('user_list')

class UserDeactivateView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot deactivate yourself.")
        else:
            user.is_active = False
            user.save()
            log_audit_event(request.user, 'USER_DEACTIVATED', 'User', user.id)
            messages.success(request, f"User {user.username} deactivated.")
        return redirect('user_list')

class UserUpdateSupervisorView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        form = SupervisorUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_audit_event(request.user, 'SUPERVISOR_ASSIGNED', 'User', user.id)
            messages.success(request, f"Supervisor updated for {user.username}.")
        else:
            messages.error(request, f"Failed to update supervisor: {form.errors}")
        return redirect('user_list')

class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        log_audit_event(self.request.user, 'PASSWORD_CHANGED', 'User', self.request.user.id)
        messages.success(self.request, "Your password has been changed successfully.")
        return response
