from django.contrib import admin

from .models import Case, CaseMember


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "title", "status", "classification", "created_by")
    search_fields = ("case_number", "title")
    list_filter = ("status", "classification")


@admin.register(CaseMember)
class CaseMemberAdmin(admin.ModelAdmin):
    list_display = ("case", "user", "role", "assigned_at")
    list_filter = ("role",)
    search_fields = ("case__case_number", "user__username")
