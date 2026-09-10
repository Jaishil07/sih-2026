def can_access_case(user, case) -> bool:
    """
    True if user is ADMIN or listed in case.members.
    """
    if not user.is_authenticated:
        return False
    if user.role == user.Role.ADMIN:
        return True
    return case.members.filter(user=user).exists()


def can_view_document(user, document) -> bool:
    """
    True if can_access_case(user, document.case).
    """
    return can_access_case(user, document.case)


def can_view_evidence(user, evidence) -> bool:
    """
    True if user is authenticated and:
    - User is ADMIN or SENIOR_OFFICER, OR
    - User is an assigned CaseMember of the evidence's case, OR
    - User is the evidence.current_custodian, OR
    - User is the to_user on an active/pending CustodyTransfer for that item.
    """
    if not user.is_authenticated:
        return False
    if user.role in [user.Role.ADMIN, user.Role.SENIOR_OFFICER]:
        return True
    if can_access_case(user, evidence.case):
        return True
    if evidence.current_custodian_id == user.id:
        return True
    from apps.evidence.models import CustodyTransfer
    if evidence.transfers.filter(to_user=user, status=CustodyTransfer.Status.PENDING).exists():
        return True
    return False

