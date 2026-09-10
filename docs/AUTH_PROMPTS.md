# AUTH_PROMPTS.md

Run these prompts in order.

## 1. Inspect
```text
Read AGENTS.md and the relevant docs.

Inspect the current Django repository.

Do not modify files.

Report:
- Django version
- apps
- settings
- URLs
- User model
- migrations
- tests

Then propose the smallest plan for:
- AbstractUser
- employee_id
- role
- department
- login/logout
- protected dashboard
- admin

Do not implement yet.
```

## 2. User
```text
Implement only the approved custom User model.

Use AbstractUser.

Add:
- employee_id
- role
- department

Integrate with Django auth/admin.
Create migrations.
Run check and tests.

Do not implement MFA, password reset or rate limiting.
```

## 3. Shared Models
```text
Create minimal model shells for:
- Case
- CaseMember
- Document
- DocumentVersion
- Evidence
- AuditLog

Only create fields required for initial relationships.

Do not implement full business logic yet.

Run makemigrations, migrate, check and tests.
```

## 4. Login
```text
Implement login/logout using Django authentication.

Requirements:
- login page
- safe invalid credentials
- inactive users denied
- protected dashboard
- logout
- CSRF

Do not implement MFA.
```

## 5. Authorization
```text
Implement reusable authorization helpers for role, case membership and document access.

Authentication is not authorization.

Prevent IDOR.

Add tests for unauthorized object access.
```

## 6. Security Review
```text
Act as a Django security reviewer.

Do not modify files.

Inspect:
- IDOR
- broken access control
- privilege escalation
- CSRF
- session issues
- secret leakage

Report severity, location, attack scenario and fix.
Wait for approval.
```

## 7. Acceptance
```text
Test:
1. Admin creates officer.
2. Officer logs in.
3. Officer accesses assigned case.
4. Officer attempts another case.
5. Access is denied.
6. Admin disables officer.
7. Officer cannot log in.

Report failures before changing code.
```
