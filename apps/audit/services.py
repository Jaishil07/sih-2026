from apps.audit.models import AuditLog

def log_audit_event(user, action, resource_type, resource_id):
    """
    Logs an audit event. 
    In a full implementation, this would handle previous_hash and event_hash chaining.
    """
    AuditLog.objects.create(
        actor=user if user and user.is_authenticated else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id)
    )
