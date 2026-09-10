from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.cases.models import Case, CaseMember

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with prototype users and cases"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting seed_data...")

        # Create Users
        users_data = [
            {
                "username": "admin",
                "role": User.Role.ADMIN,
                "department": "Administration",
                "employee_id": "EMP-001",
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "username": "officer_a",
                "role": User.Role.INVESTIGATING_OFFICER,
                "department": "Cyber Crime",
                "employee_id": "EMP-101",
            },
            {
                "username": "officer_b",
                "role": User.Role.INVESTIGATING_OFFICER,
                "department": "Narcotics",
                "employee_id": "EMP-102",
            },
            {
                "username": "judge",
                "role": User.Role.COURT_USER,
                "department": "Judiciary",
                "employee_id": "EMP-301",
            },
        ]

        created_users = {}
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "role": data["role"],
                    "department": data["department"],
                    "employee_id": data["employee_id"],
                    "is_staff": data.get("is_staff", False),
                    "is_superuser": data.get("is_superuser", False),
                },
            )
            if created:
                user.set_password("DemoPass@2026")
                user.save()
            created_users[data["username"]] = user

        self.stdout.write("Users seeded.")

        # Create Case
        case, created = Case.objects.get_or_create(
            case_number="CR-2026-00124",
            defaults={
                "title": "Illegal Cyber Intrusion and Extortion Investigation",
                "classification": "CONFIDENTIAL",
                "created_by": created_users["admin"],
            },
        )
        
        if created:
            CaseMember.objects.create(
                case=case,
                user=created_users["officer_a"],
                role="Lead Investigator"
            )
        
        self.stdout.write("Case CR-2026-00124 seeded.")
        self.stdout.write(self.style.SUCCESS("Database seeding complete."))
