from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.

    Extends Django's built-in UserAdmin so that employee_id, role,
    and department appear in the admin interface alongside the
    standard username/password/email fields.
    """

    # List view columns
    list_display = (
        "username",
        "employee_id",
        "role",
        "department",
        "is_active",
        "is_staff",
    )
    list_filter = BaseUserAdmin.list_filter + ("role", "department")
    search_fields = BaseUserAdmin.search_fields + ("employee_id",)

    # Detail view: add our custom fields to the existing fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "SIH Profile",
            {
                "fields": ("employee_id", "role", "department"),
            },
        ),
    )

    # Creation form: include our custom fields
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "SIH Profile",
            {
                "fields": ("employee_id", "role", "department"),
            },
        ),
    )
