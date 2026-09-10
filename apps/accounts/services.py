def can_access_case(user, case) -> bool:
    """
    True if user is ADMIN or AUDITOR, or listed in case.members.
    """
    if not user.is_authenticated:
        return False
    if user.role in [user.Role.ADMIN, user.Role.AUDITOR]:
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
    - User is ADMIN, AUDITOR or SENIOR_OFFICER, OR
    - User is an assigned CaseMember of the evidence's case, OR
    - User is the evidence.current_custodian, OR
    - User is the to_user on an active/pending CustodyTransfer for that item.
    """
    if not user.is_authenticated:
        return False
    if user.role in [user.Role.ADMIN, user.Role.AUDITOR, user.Role.SENIOR_OFFICER]:
        return True
    if can_access_case(user, evidence.case):
        return True
    if evidence.current_custodian_id == user.id:
        return True
    from apps.evidence.models import CustodyTransfer
    if evidence.transfers.filter(to_user=user, status=CustodyTransfer.Status.PENDING).exists():
        return True
    return False


def can_delete_document(user, document) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == user.Role.ADMIN:
        return True
    if user.role == user.Role.SENIOR_OFFICER and document.case.members.filter(user=user).exists():
        return True
    return False


def can_upload_document(user, case) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == user.Role.ADMIN:
        return True
    if user.role in [user.Role.SENIOR_OFFICER, user.Role.INVESTIGATING_OFFICER, user.Role.FORENSIC_OFFICER]:
        return case.members.filter(user=user).exists()
    return False


def can_close_case(user, case) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == user.Role.ADMIN:
        return True
    if user.role == user.Role.SENIOR_OFFICER and case.members.filter(user=user).exists():
        return True
    return False


def can_assign_officer(user, case) -> bool:
    return can_close_case(user, case)


def can_approve_evidence(user, evidence) -> bool:
    if not user.is_authenticated:
        return False
    if user.role == user.Role.ADMIN:
        return True
    if user.role == user.Role.SENIOR_OFFICER and evidence.case.members.filter(user=user).exists():
        return True
    return False

