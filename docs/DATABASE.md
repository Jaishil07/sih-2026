# DATABASE.md

## Database
Use SQLite for the internal prototype. Use Django ORM only.

## User
Extend `AbstractUser` with:
- employee_id
- role
- department

## Case
- case_number
- title
- description
- status
- classification
- created_by
- timestamps

## CaseMember
- case
- user
- role
- assigned_at

## Document
- case
- title
- document_type
- classification
- status
- created_by
- timestamps

## DocumentVersion
- document
- version_number
- file
- sha256_hash
- created_by
- timestamp
- change_reason

## Evidence
- case
- evidence_number
- description
- current_custodian
- created_at

## CustodyTransfer
- evidence
- from_user
- to_user
- timestamp
- reason
- location

## AuditLog
- actor
- action
- resource_type
- resource_id
- timestamp
- previous_hash
- event_hash

## AI
DocumentText:
- document
- extracted_text
- extraction_method

AIResult:
- document
- result_type
- result
- created_at

## Migration Order
User → Case → CaseMember → Document → DocumentVersion → Evidence → CustodyTransfer → AuditLog → DocumentText → AIResult

## Rules
```bash
python manage.py makemigrations
python manage.py migrate
```

Commit migration files. Do not casually rewrite shared migrations.

## Seed
```bash
python manage.py seed_data
```

Seed `admin`, `officer_a`, `officer_b`, `judge` and `CR-2026-00124`.
