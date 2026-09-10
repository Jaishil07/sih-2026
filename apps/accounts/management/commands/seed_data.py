from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.cases.models import Case, CaseMember, PersonOfInterest
from apps.evidence.models import Evidence, CustodyTransfer
from django.utils import timezone

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
                "username": "senior_officer",
                "role": User.Role.SENIOR_OFFICER,
                "department": "Cyber Crime",
                "employee_id": "EMP-050",
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

        # Set supervisors
        officer_a = created_users["officer_a"]
        officer_b = created_users["officer_b"]
        senior_officer = created_users["senior_officer"]
        
        officer_a.supervisor = senior_officer
        officer_b.supervisor = senior_officer
        officer_a.save()
        officer_b.save()

        self.stdout.write("Users and hierarchy seeded.")

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
        
        # Add POI
        PersonOfInterest.objects.get_or_create(
            case=case,
            name="Vikram Malhotra",
            defaults={
                "alias": "ShadowByte",
                "role_in_case": PersonOfInterest.Role.SUSPECT,
                "notes": "Alleged operator of unauthorized exfiltration servers"
            }
        )

        # Add Evidence
        evidence, created_ev = Evidence.objects.get_or_create(
            evidence_number="EV-2026-0091",
            defaults={
                "case": case,
                "description": "Seized encrypted NVMe SSD from raid location",
                "current_custodian": created_users["officer_a"],
                "status": Evidence.Status.APPROVED,
                "approved_by": created_users["senior_officer"],
                "approved_at": timezone.now()
            }
        )
        if created_ev:
            CustodyTransfer.objects.create(
                evidence=evidence,
                from_user=None,
                to_user=created_users["officer_a"],
                reason="Initial Collection",
                location="Raid Location"
            )

        self.stdout.write("Case CR-2026-00124 and related data seeded.")
        self.stdout.write(self.style.SUCCESS("Database seeding complete."))
