# PROJECT_SPEC.md

## Objective
Build a secure, case-centric Digital Document and Evidence Management System for legal and investigation workflows.

## Prototype Users
- ADMIN
- INVESTIGATING_OFFICER
- FORENSIC_OFFICER
- COURT_USER

## P0
- login/logout
- employee ID, role, department
- case creation and membership
- document upload
- document metadata
- document versions
- SHA-256 integrity
- audit trail
- object-level access control

## P1
- evidence custody
- AI classification
- entity extraction
- summary
- search

## Deferred
- MFA/TOTP
- password reset
- rate limiting
- PostgreSQL
- Tesseract
- digital-signature PKI
- blockchain
- enterprise SSO
- production deployment

## Central Demo
Upload → Hash → Audit → AI → Search → Access Denied → Version → Tamper Detection.
