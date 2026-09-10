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
    True if can_access_case(user, evidence.case).
    """
    return can_access_case(user, evidence.case)
