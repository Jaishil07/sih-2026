# TESTING.md

## Goal
Protect the demo-critical behavior.

## Authentication
- valid login
- invalid password
- inactive user
- logout

## Authorization
- assigned case allowed
- unassigned case denied
- role restriction
- URL/object manipulation denied

## Documents
- upload
- invalid upload
- version
- authorized download
- unauthorized download

## Integrity
- valid hash
- modified file detected

## Audit
- event generated
- chain valid
- altered event detected

## AI
- valid JSON
- malformed response
- API failure

## Commands
```bash
python manage.py check
python manage.py test
```

## Manual Acceptance
1. Login as officer_a.
2. Open CR-2026-00124.
3. Upload document.
4. Verify hash.
5. Generate AI summary.
6. Search.
7. Login as officer_b.
8. Attempt access.
9. Verify denial.
10. Modify demo file.
11. Verify tamper detection.
