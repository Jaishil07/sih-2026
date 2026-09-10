from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.cases.models import Case, CaseMember, PersonOfInterest, CaseNote
from apps.accounts.models import User
from apps.accounts.services import can_access_case
from apps.audit.services import log_audit_event

class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = "cases/case_list.html"
    context_object_name = "cases"

    def get_queryset(self):
        if self.request.user.role == self.request.user.Role.ADMIN:
            return Case.objects.all()
        return Case.objects.filter(members__user=self.request.user)

@login_required
def case_detail_view(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if not can_access_case(request.user, case):
        log_audit_event(request.user, "CASE_ACCESS_DENIED", "Case", case.id)
        raise PermissionDenied

    log_audit_event(request.user, "CASE_VIEWED", "Case", case.id)
    
    # Pre-fetch required relations for tabs
    documents = case.documents.all().order_by('-created_at')
    evidence_items = case.evidence_items.all().order_by('-created_at')
    persons_of_interest = case.persons_of_interest.all().order_by('-created_at')
    members = case.members.select_related('user').all()
    notes = case.notes.select_related('author').all()
    
    # Available users for assignment (admins/seniors can assign)
    available_users = User.objects.exclude(id__in=members.values_list('user_id', flat=True))

    return render(request, "cases/case_detail.html", {
        "case": case,
        "documents": documents,
        "evidence_items": evidence_items,
        "persons_of_interest": persons_of_interest,
        "members": members,
        "notes": notes,
        "available_users": available_users
    })

@login_required
def add_person_of_interest_view(request, pk):
    if request.method != 'POST':
        return redirect('case_detail', pk=pk)
        
    case = get_object_or_404(Case, pk=pk)
    if not can_access_case(request.user, case):
        raise PermissionDenied

    name = request.POST.get('name')
    alias = request.POST.get('alias', '')
    role_in_case = request.POST.get('role_in_case')
    identification_number = request.POST.get('identification_number', '')
    notes = request.POST.get('notes', '')

    poi = PersonOfInterest.objects.create(
        case=case,
        name=name,
        alias=alias,
        role_in_case=role_in_case,
        identification_number=identification_number,
        notes=notes
    )
    
    log_audit_event(request.user, 'PERSON_OF_INTEREST_ADDED', 'PersonOfInterest', poi.id)
    messages.success(request, f"Person of interest '{name}' added successfully.")
    
    return redirect('case_detail', pk=case.id)

@login_required
def assign_member_view(request, pk):
    if request.method != 'POST':
        return redirect('case_detail', pk=pk)
        
    case = get_object_or_404(Case, pk=pk)
    
    # Only ADMIN or SENIOR_OFFICER can assign members
    if request.user.role not in [request.user.Role.ADMIN, request.user.Role.SENIOR_OFFICER]:
        messages.error(request, "Only Admins or Senior Officers can assign case members.")
        return redirect('case_detail', pk=case.id)

    user_id = request.POST.get('user_id')
    role = request.POST.get('role', 'Investigator')
    
    user_to_assign = get_object_or_404(User, id=user_id)
    
    CaseMember.objects.get_or_create(
        case=case,
        user=user_to_assign,
        defaults={'role': role}
    )
    
    log_audit_event(request.user, 'MEMBER_ASSIGNED', 'Case', case.id, details={'assigned_user_id': user_to_assign.id})
    messages.success(request, f"{user_to_assign.username} assigned to case.")
    
    return redirect('case_detail', pk=case.id)

@login_required
def add_case_note_view(request, pk):
    if request.method != 'POST':
        return redirect('case_detail', pk=pk)
        
    case = get_object_or_404(Case, pk=pk)
    if not can_access_case(request.user, case):
        raise PermissionDenied

    content = request.POST.get('content')
    if content:
        note = CaseNote.objects.create(
            case=case,
            author=request.user,
            content=content
        )
        log_audit_event(request.user, 'CASE_NOTE_ADDED', 'CaseNote', note.id)
        messages.success(request, "Case note added successfully.")
        
    return redirect('case_detail', pk=case.id)
