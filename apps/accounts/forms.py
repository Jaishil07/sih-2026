from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    initial_password = forms.CharField(widget=forms.PasswordInput(), required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'employee_id', 'role', 'department', 'designation', 'supervisor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter supervisors to only SENIOR_OFFICER or ADMIN
        self.fields['supervisor'].queryset = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.SENIOR_OFFICER])
        self.fields['supervisor'].required = False

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['initial_password'])
        if commit:
            user.save()
        return user

class SupervisorUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['supervisor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervisor'].queryset = User.objects.filter(role__in=[User.Role.ADMIN, User.Role.SENIOR_OFFICER])
        
    def clean_supervisor(self):
        supervisor = self.cleaned_data.get('supervisor')
        if supervisor and supervisor == self.instance:
            raise forms.ValidationError("User cannot be their own supervisor.")
        # Optional: check circular assignment, but maybe skip for prototype
        return supervisor
