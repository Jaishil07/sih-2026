from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "resource_type", "resource_id", "timestamp")
    list_filter = ("action", "resource_type")
    search_fields = ("actor__username", "resource_id", "event_hash")
