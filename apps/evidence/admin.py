from django.contrib import admin

from .models import CustodyTransfer, Evidence


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("evidence_number", "case", "current_custodian", "created_at")
    search_fields = ("evidence_number", "case__case_number")


@admin.register(CustodyTransfer)
class CustodyTransferAdmin(admin.ModelAdmin):
    list_display = ("evidence", "from_user", "to_user", "timestamp")
    search_fields = ("evidence__evidence_number",)
