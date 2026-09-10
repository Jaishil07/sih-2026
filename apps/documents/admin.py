from django.contrib import admin

from .models import Document, DocumentVersion


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "case", "document_type", "classification", "status")
    search_fields = ("title", "case__case_number")
    list_filter = ("classification", "status", "document_type")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "sha256_hash", "is_signed")
    search_fields = ("document__title", "sha256_hash")
    list_filter = ("is_signed",)
