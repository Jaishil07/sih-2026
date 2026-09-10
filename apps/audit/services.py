import hashlib
import json
from django.utils import timezone
from apps.audit.models import AuditLog

def calculate_event_hash(actor_id, action, resource_type, resource_id, timestamp_str, previous_hash, details_json) -> str:
    """Generates SHA-256 hash for the audit event."""
    data_string = f"{actor_id}|{action}|{resource_type}|{resource_id}|{timestamp_str}|{previous_hash}|{details_json}"
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def log_audit_event(actor, action, resource_type, resource_id, request=None, details=None) -> AuditLog:
    """Logs an audit event with cryptographic hash chaining."""
    details = details or {}
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    last_log = AuditLog.objects.order_by('-id').first()
    previous_hash = last_log.event_hash if last_log else "0" * 64

    now = timezone.now()
    timestamp_str = now.strftime('%Y-%m-%dT%H:%M:%S')
    details_json = json.dumps(details, sort_keys=True)
    actor_id = actor.id if actor and actor.is_authenticated else "None"
    
    event_hash = calculate_event_hash(
        actor_id, action, resource_type, str(resource_id), timestamp_str, previous_hash, details_json
    )

    log_entry = AuditLog(
        actor=actor if actor and actor.is_authenticated else None,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        ip_address=ip_address,
        details=details,
        previous_hash=previous_hash,
        event_hash=event_hash,
        # Override the auto_now_add to exactly match what we hashed
    )
    log_entry.timestamp = now
    log_entry.save()
    return log_entry

def verify_audit_chain() -> tuple[bool, int | None]:
    """
    Iterates through all audit records in chronological order.
    Returns (True, None) if unbroken, or (False, broken_log_id) if corrupted/tampered.
    """
    logs = AuditLog.objects.all().order_by('id')
    expected_previous = "0" * 64

    for log in logs:
        if log.previous_hash != expected_previous:
            return False, log.id

        timestamp_str = log.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
        details_json = json.dumps(log.details, sort_keys=True)
        actor_id = log.actor_id if log.actor_id else "None"

        computed_hash = calculate_event_hash(
            actor_id, log.action, log.resource_type, log.resource_id, timestamp_str, log.previous_hash, details_json
        )

        if log.event_hash != computed_hash:
            return False, log.id

        expected_previous = log.event_hash

    return True, None
