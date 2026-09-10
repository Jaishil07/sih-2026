from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.cases.models import Case, PersonOfInterest, CaseNote
from apps.documents.models import Document
from apps.evidence.models import Evidence

@login_required
def global_search_view(request):
    query = request.GET.get('q', '').strip()
    case_filter = request.GET.get('case_id', '')
    
    user = request.user
    
    # Base user cases
    if user.role == user.Role.ADMIN:
        user_cases = Case.objects.all()
    else:
        user_cases = Case.objects.filter(members__user=user)
        
    if case_filter:
        user_cases = user_cases.filter(id=case_filter)
        
    case_ids = user_cases.values_list('id', flat=True)

    results = {
        'documents': [],
        'suspects': [],
        'evidence': [],
        'notes': []
    }

    if query:
        # Search Documents
        # Match title, document_type, raw extracted text, and AI summary
        docs = Document.objects.filter(case_id__in=case_ids).filter(
            Q(title__icontains=query) |
            Q(document_type__icontains=query) |
            Q(extracted_text__raw_text__icontains=query) |
            Q(ai_results__summary__icontains=query)
        ).distinct()
        results['documents'] = docs

        # Search POIs
        pois = PersonOfInterest.objects.filter(case_id__in=case_ids).filter(
            Q(name__icontains=query) |
            Q(alias__icontains=query) |
            Q(identification_number__icontains=query) |
            Q(notes__icontains=query)
        ).distinct()
        results['suspects'] = pois

        # Search Evidence
        evidences = Evidence.objects.filter(case_id__in=case_ids).filter(
            Q(evidence_number__icontains=query) |
            Q(description__icontains=query)
        ).distinct()
        results['evidence'] = evidences

        # Search Notes
        notes = CaseNote.objects.filter(case_id__in=case_ids).filter(
            Q(content__icontains=query)
        ).distinct()
        results['notes'] = notes

    all_cases = Case.objects.all() if user.role == user.Role.ADMIN else Case.objects.filter(members__user=user)

    return render(request, 'search/search_results.html', {
        'query': query,
        'results': results,
        'all_cases': all_cases,
        'selected_case': int(case_filter) if case_filter else None
    })
