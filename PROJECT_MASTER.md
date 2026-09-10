# SIH26190 Prototype Project Plan
## Binding Scope and Architecture Override

**Version:** 2.0 — Internal College Prototype  
**Date:** 7 September 2026  
**Internal round:** Thursday-Friday, 10-11 September 2026  
**Team:** 6  
**Technical lead:** Member 1

> **This section overrides any earlier enterprise-oriented details in this document.**

### Prototype-first rules

1. **SQLite is the development database.** Do not require SQLite (prototype; PostgreSQL later) for the internal round.
2. **MFA (deferred)/TOTP is deferred.** Use normal Django authentication and roles.
3. **Password reset and rate limiting are deferred.**
4. **Tesseract (deferred) is deferred.** Use `pypdf`/`pdfplumber` for digital PDFs and approved Gemini/vision extraction where useful.
5. **Digital-signature PKI is deferred.** SHA-256 + user/session identity + versions + audit are sufficient for the prototype.
6. **Blockchain (deferred) is deferred.** Use a hash-chained audit log.
7. **React is deferred.** Use Django Templates + HTML/CSS/JavaScript.
8. **Microservices are rejected.** Use one modular Django monolith.
9. **The initial database schema should be created early as minimal model shells so all six members can work in parallel.**
10. **The P0 demo narrative is:**

```text
Login
 ↓
Role-based access
 ↓
Case
 ↓
Upload document
 ↓
SHA-256
 ↓
Audit
 ↓
AI extraction/classification/summary
 ↓
Search
 ↓
Unauthorized access → DENIED
 ↓
Controlled modification → TAMPER DETECTED
```

### P0

- Django project;
- custom User;
- role/department/employee ID;
- login/logout;
- cases;
- case membership;
- document upload;
- document versions;
- SHA-256;
- audit chain;
- access control.

### P1

- evidence custody;
- AI classification;
- entity extraction;
- summary;
- search.

### P2 / future

- MFA (deferred);
- password reset;
- rate limiting;
- SQLite (prototype; PostgreSQL later);
- Tesseract (deferred);
- digital signatures (deferred);
- blockchain (deferred);
- production deployment.

### Immediate shared-schema strategy

The technical lead creates minimal shells for:

```text
User
Case
CaseMember
Document
DocumentVersion
Evidence
AuditLog
```

Then runs the first migration and pushes it to `develop`.

This unblocks Members 2-6 immediately.

### SQLite rationale

SQLite removes database-server setup, credentials and cross-platform problems for six beginner developers. Django ORM must be used so SQLite (prototype; PostgreSQL later) can be introduced later.

### Seed data

Create:

```bash
python manage.py seed_data
```

with:

```text
admin
officer_a
officer_b
judge

Case: CR-2026-00124
```

Use only synthetic data.

---

# SIH26190 Master Project Plan
## Secure Digital Document Management System for Legal and Investigation Documents

**Version:** 1.0  
**Prepared:** 7 September 2026  
**Hackathon window assumed:** Thursday-Friday following preparation week  
**Team size:** 6  
**Primary development approach:** AI-assisted Django monolith  
**Technical lead:** Member 1 / Django lead

---

# 1. Purpose of This Document

This document is the team's canonical project reference.

It is intended to be:

- shared with all six team members;
- supplied as context to AI coding agents such as Antigravity;
- reused in fresh AI conversations when a previous conversation becomes too long;
- used to keep architecture, terminology, priorities and implementation decisions consistent;
- used as the basis for development, testing and the final demonstration.

When an AI agent receives this document, it should treat it as project context, not as an invitation to redesign the application.

If a later technical decision conflicts with this document, the team must explicitly decide whether to update this document before allowing the new architecture to propagate.

---

# 2. Problem Statement

## SIH26190

**Title:** Secure Digital Document Management System for Legal and Investigation Documents

**Organization:** Ministry of Home Affairs  
**Category:** Software  
**Theme:** Miscellaneous

The problem concerns the handling of large volumes of sensitive legal and investigation documents by law-enforcement agencies, courts, legal departments and investigative organizations.

The documents involved can include:

- FIRs and police reports
- Investigation records
- Witness statements
- Charge sheets
- Court filings
- Evidence records
- Forensic reports
- Legal notices
- Judgments

The problem statement identifies the use of paper-based systems and fragmented digital storage as sources of operational problems, including:

- difficulty locating documents;
- unauthorized access to confidential information;
- document tampering risks;
- lack of version control;
- inefficient collaboration between departments;
- delays in legal and investigative processes;
- poor auditability and compliance tracking.

The stated need is for a secure, centralized and intelligent document-management system that preserves data integrity, accessibility, confidentiality and efficient case management.

The problem statement specifically points to modern technologies such as:

- Cloud Computing
- Artificial Intelligence
- Blockchain (deferred)
- Digital Signatures
- Secure Access Control

as technologies that can improve the management and security of legal and investigative documents.

## Problem description

The objective is to develop a Secure Digital Document Management System that enables law-enforcement agencies, legal institutions and investigative departments to securely:

- store;
- organize;
- manage;
- retrieve;
- share

sensitive legal and investigation documents.

The system should:

1. Digitize and centralize document storage.
2. Ensure secure access and confidentiality.
3. Prevent unauthorized modifications.
4. Maintain a complete audit trail of document activities.
5. Enable efficient document search and retrieval.
6. Support collaboration among authorized stakeholders.
7. Ensure compliance with legal and regulatory requirements.

The overall challenge is to create a secure, scalable and intelligent platform that streamlines document handling while preserving legal validity and evidentiary integrity.

### Source note

The indexed 2026 problem-statement mirrors consistently reproduce the above background and description. Some unofficial mirrors currently show a corrupted/mismatched "Expected Solution" field for SIH26190 that refers to monitoring police assets. That line conflicts with the SIH26190 title and the detailed background/description, so this project plan does **not** treat that corrupted line as a requirement. The clearly stated DMS requirements above are the basis for this plan.

---

# 3. Our Interpretation of the Problem

We are not building "Google Drive for police."

The proposed system is a secure case-centric document and evidence platform in which every sensitive document has:

- an identity;
- a case association;
- a classification;
- an owner/creator;
- access rules;
- versions;
- an integrity hash;
- optionally a digital signature;
- an audit history;
- and, where relevant, an evidence chain of custody.

The central idea is:

> **Every important document should have a verifiable lifecycle.**

The lifecycle is:

```text
Create/Upload
      ↓
Authenticate
      ↓
Authorize
      ↓
Store securely
      ↓
Hash
      ↓
Version
      ↓
OCR / Index
      ↓
Use / Share
      ↓
Sign if required
      ↓
Audit
      ↓
Verify integrity
      ↓
Archive
```

---

# 4. Proposed Solution

We will build a **Django-based secure digital document management system** for legal and investigation workflows.

The application will use a modular Django monolith rather than a distributed microservice architecture.

The proposed stack is:

| Layer | Technology |
|---|---|
| Backend | Python + Django |
| Database | SQLite (prototype; PostgreSQL later) |
| Frontend | Django Templates + HTML/CSS/JavaScript |
| UI | Bootstrap or Tailwind, kept simple |
| AI | Gemini API / approved LLM provider |
| OCR | Tesseract (deferred) or another approved OCR engine |
| Search | SQLite (prototype; PostgreSQL later) full-text search initially; OpenSearch only if justified |
| File storage | Django storage initially; S3/MinIO-compatible storage if needed |
| Authentication | Django authentication |
| Password hashing | Django's built-in password hashing |
| Integrity | SHA-256 |
| Digital signatures (deferred) | Established cryptographic library |
| Versioning | Application/database model |
| Audit | Hash-chained audit records |
| Source control | Git + GitHub |
| AI development | Antigravity + other AI assistants |
| Deployment | Local/demo deployment first; production-style hardening only where useful |

## Why Django?

The team is inexperienced, so the architecture must minimize the amount of infrastructure we have to invent.

Django already provides mature building blocks for:

- authentication;
- sessions;
- password handling;
- forms;
- CSRF protection;
- ORM/database access;
- admin;
- file handling;
- testing;
- security middleware.

This allows the team to focus on the actual SIH problem instead of spending the hackathon building infrastructure.

---

# 5. Core Product Concept

The application's central object is the **Case**.

A case contains authorized users, documents and evidence.

```text
CASE-2026-00124
│
├── FIR
├── Investigation Report
├── Witness Statements
├── Forensic Reports
├── Charge Sheet
├── Court Filings
│
└── Evidence
    ├── E-001
    ├── E-002
    └── E-003
```

Each document has versions:

```text
Forensic_Report.pdf
│
├── Version 1
├── Version 2
└── Version 3 ✓ Digitally Signed
```

Each important action produces an audit event:

```text
Officer A uploaded document
Officer B viewed document
Officer C attempted unauthorized access
Officer A created Version 2
Officer A digitally signed Version 2
Evidence transferred from Officer A to Forensic Lab
```

---

# 6. The Security Model

Security is not one feature. It is a chain.

```text
Identity
   ↓
Authentication
   ↓
MFA (deferred)
   ↓
Authorization
   ↓
Case membership
   ↓
Document permissions
   ↓
Classification
   ↓
Integrity
   ↓
Auditability
```

## 6.1 Authentication

Users must authenticate before accessing protected resources.

Use:

- Django authentication;
- strong password validation;
- secure sessions;
- MFA (deferred)/TOTP;
- account activation/deactivation;
- login attempt protection;
- password reset.

## 6.2 Authorization

Authentication answers:

> Who are you?

Authorization answers:

> Are you allowed to perform this action on this particular resource?

A user being logged in must never automatically imply access to every case or document.

## 6.3 Roles

Initial roles:

- ADMIN
- SENIOR_OFFICER
- INVESTIGATING_OFFICER
- FORENSIC_OFFICER
- PROSECUTOR
- COURT_USER
- AUDITOR

## 6.4 Permissions

Initial application permissions:

- CASE_VIEW
- CASE_CREATE
- CASE_EDIT
- CASE_ASSIGN
- DOCUMENT_VIEW
- DOCUMENT_UPLOAD
- DOCUMENT_EDIT
- DOCUMENT_DOWNLOAD
- DOCUMENT_SHARE
- DOCUMENT_SIGN
- EVIDENCE_VIEW
- EVIDENCE_CREATE
- EVIDENCE_TRANSFER
- AUDIT_VIEW
- USER_MANAGE

Use Django's permission framework where appropriate.

## 6.5 ABAC-style restrictions

Beyond roles, access can depend on:

- case membership;
- department;
- document classification;
- security clearance;
- document state.

Example:

```text
User:
Role = INVESTIGATING_OFFICER
Department = Cyber Crime

Document:
Case = CR-1024
Department = Cyber Crime
Classification = CONFIDENTIAL

Result:
Allowed only if the user is a member of CR-1024 and
satisfies the classification rules.
```

---

# 7. Document Integrity

Every uploaded document version receives a SHA-256 hash.

```text
file bytes
    ↓
SHA-256
    ↓
stored hash
```

Later:

```text
stored hash
      vs
newly calculated hash
```

If they differ:

```text
DOCUMENT INTEGRITY COMPROMISED
```

This is one of the primary SIH demonstration features.

Important rule:

**The hash must be calculated from the actual file bytes, not from the filename or metadata.**

---

# 8. Version Control

Legal/investigation documents must not simply be overwritten.

Instead:

```text
Document
│
├── Version 1
├── Version 2
├── Version 3
└── Version 4 ✓ Final/Signed
```

Each version stores:

- version number;
- file;
- SHA-256 hash;
- creator;
- timestamp;
- change reason;
- signature status.

Finalized/signed versions should be treated as immutable.

---

# 9. Digital Signatures

Digital signatures (deferred) provide stronger evidence of authorship/integrity than a simple hash.

Conceptually:

```text
Document
   ↓
Hash
   ↓
Private key
   ↓
Digital signature
```

Verification:

```text
Document
   ↓
Hash
   ↓
Public key
   ↓
Signature verification
```

Do not implement cryptographic algorithms ourselves.

Use an established cryptographic library.

---

# 10. Evidence Chain of Custody

Evidence is not merely another document.

Each evidence item has a custody lifecycle:

```text
Collected by Officer A
        ↓
Transferred to Forensic Officer B
        ↓
Forensic analysis
        ↓
Returned to Officer A
        ↓
Submitted to Court
```

Each transfer records:

- evidence ID;
- previous custodian;
- new custodian;
- timestamp;
- reason;
- location where appropriate;
- evidence/document hash where applicable;
- signature where applicable;
- audit event.

This creates a demonstrable chain of custody.

---

# 11. Audit Trail

Important actions generate audit events.

Examples:

- LOGIN_SUCCESS
- LOGIN_FAILURE
- LOGOUT
- MFA (deferred)_SUCCESS
- MFA (deferred)_FAILURE
- DOCUMENT_VIEWED
- DOCUMENT_UPLOADED
- DOCUMENT_DOWNLOADED
- DOCUMENT_MODIFIED
- DOCUMENT_SHARED
- DOCUMENT_SIGNED
- ACCESS_DENIED
- PERMISSION_CHANGED
- EVIDENCE_TRANSFERRED
- ACCOUNT_ACTIVATED
- ACCOUNT_DEACTIVATED

## Hash-chained audit log

Each audit event contains the hash of the previous event.

```text
Event 1
  ↓ hash
Event 2
  ↓ hash
Event 3
  ↓ hash
Event 4
```

If Event 2 is modified:

```text
Event 2 hash changes
        ↓
Event 3 previous_hash no longer matches
        ↓
CHAIN BROKEN
```

The UI should show:

```text
✓ Audit chain valid
```

or:

```text
⚠ Audit chain integrity failure
```

---

# 12. OCR

Scanned legal documents may contain no machine-readable text.

Pipeline:

```text
Scanned PDF/image
        ↓
OCR
        ↓
Extracted text
        ↓
Search index
```

For the prototype, Tesseract (deferred) is a practical starting point.

OCR results must be treated as extracted data, not automatically as authoritative legal facts.

---

# 13. Search

Search should work at multiple levels.

## Metadata search

Examples:

- case number;
- document type;
- classification;
- date;
- officer;
- evidence ID.

## Filename search

Example:

```text
forensic_report
```

## Full-text search

Search the OCR/extracted text.

Example:

```text
mobile device forensic report
```

## AI-assisted search

Natural-language query:

```text
Find forensic reports related to mobile devices
in Case CR-1024.
```

AI may help interpret the query, but authorization must still be enforced by normal application logic.

---

# 14. AI Features

AI is a major part of our implementation, but AI must **assist** rather than control security.

## 14.1 Document classification

Input:

- document text;
- metadata.

Output:

- suggested document type;
- suggested classification.

The user must be able to review/override the result.

## 14.2 Entity extraction

Extract:

- persons;
- organizations;
- locations;
- dates;
- case numbers;
- evidence IDs.

## 14.3 Summarization

Generate:

- short summary;
- key findings;
- important dates;
- people mentioned;
- evidence referenced.

## 14.4 Semantic/natural-language search

Use AI to help map user language to relevant indexed content.

## 14.5 AI restrictions

AI must never independently:

- authorize a user;
- change permissions;
- delete evidence;
- modify audit records;
- alter custody history;
- make legal decisions.

---

# 15. Security Classification

Suggested classifications:

- PUBLIC
- INTERNAL
- CONFIDENTIAL
- HIGHLY_CONFIDENTIAL
- EVIDENCE

Classification is an access-control attribute, not just a visual label.

---

# 16. Secure Sharing

Documents should not be exposed through predictable public URLs.

Bad:

```text
/documents/123/
```

with no authorization check.

Correct conceptual flow:

```text
Request
  ↓
Authentication
  ↓
Authorization
  ↓
Resource check
  ↓
Return document
  ↓
Audit event
```

If temporary links are implemented, they should be:

- time-limited;
- scoped;
- permission checked;
- auditable.

---

# 17. Database Architecture

SQLite (prototype; PostgreSQL later) is the primary database.

Initial conceptual schema:

```text
users
departments
roles
permissions

cases
case_members

documents
document_versions
document_permissions

evidence
custody_transfers

audit_logs
security_events
security_alerts

document_text
document_entities
ai_results
```

## 17.1 User

Fields conceptually include:

- id;
- employee_id;
- name;
- email;
- department;
- designation;
- role;
- security clearance;
- active status;
- password hash;
- timestamps.

Prefer Django's User/auth system instead of manually implementing passwords.

## 17.2 Case

- id;
- case_number;
- title;
- description;
- status;
- classification;
- created_by;
- timestamps.

## 17.3 CaseMember

- case;
- user;
- role;
- assigned_at.

## 17.4 Document

- id;
- case;
- title;
- document_type;
- classification;
- status;
- current_version;
- created_by;
- timestamps.

## 17.5 DocumentVersion

- id;
- document;
- version_number;
- file;
- sha256_hash;
- created_by;
- timestamp;
- change_reason;
- is_signed.

## 17.6 Evidence

- id;
- case;
- evidence_number;
- description;
- current_custodian;
- timestamp.

## 17.7 CustodyTransfer

- evidence;
- from_user;
- to_user;
- timestamp;
- reason;
- location;
- evidence_hash.

## 17.8 AuditLog

- id;
- actor;
- action;
- resource_type;
- resource_id;
- timestamp;
- IP address where appropriate;
- previous_hash;
- event_hash.

## 17.9 AI data

DocumentText:

- document;
- extracted_text;
- extraction_method.

AIResult:

- document;
- result_type;
- result;
- created_at.

---

# 18. Database Configuration Plan

The team should use SQLite (prototype; PostgreSQL later) rather than SQLite for the real project.

## Development environment

Each developer should have:

```text
Python
venv
Django
SQLite for the internal prototype; SQLite (prototype; PostgreSQL later) later
Git
Antigravity
```

## Environment variables

Never commit secrets.

Example `.env`:

```text
DJANGO_SECRET_KEY=...
DEBUG=True
DATABASE_NAME=sih26190
DATABASE_USER=sih_user
DATABASE_PASSWORD=...
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432
GEMINI_API_KEY=...
```

`.env` must be in `.gitignore`.

Provide `.env.example`:

```text
DJANGO_SECRET_KEY=
DEBUG=True

DATABASE_NAME=
DATABASE_USER=
DATABASE_PASSWORD=
DATABASE_HOST=127.0.0.1
DATABASE_PORT=5432

GEMINI_API_KEY=
```

## Django settings

Use environment variables rather than hard-coded credentials.

Development may use:

```text
127.0.0.1:5432
```

Production/demo deployment should use appropriate secrets and HTTPS.

## Migration rule

Never edit an already-created migration just because it is inconvenient.

Create a new migration.

Never delete migrations from the shared repository to "fix" a schema problem without understanding the consequences.

---

# 19. Django Project Structure

Recommended structure:

```text
sih26190-dms/
│
├── AGENTS.md
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
├── manage.py
│
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── cases/
│   ├── documents/
│   ├── evidence/
│   ├── audit/
│   └── ai_assistant/
│
├── templates/
├── static/
├── media/
│
└── docs/
    ├── PROJECT_SPEC.md
    ├── ARCHITECTURE.md
    ├── DATABASE.md
    ├── SECURITY.md
    ├── AI_FEATURES.md
    ├── UI_SPEC.md
    └── TESTING.md
```

A Django monolith is intentional.

Do not add:

- React;
- Node backend;
- microservices;
- Kubernetes;
- unnecessary queues;
- unnecessary cloud infrastructure.

unless a real requirement appears.

---

# 20. Six-Person Team Structure

## Member 1 — Django Lead / Technical Lead

Primary ownership:

- Django project;
- settings;
- URL architecture;
- accounts;
- authentication;
- authorization;
- database integration;
- code review;
- architectural consistency;
- final integration.

This is the user/team member with the strongest current Python/HTML/CSS/JS knowledge.

## Member 2 — Case & Document Management

Own:

- cases;
- case members;
- document model;
- upload/download;
- document metadata;
- document versions;
- storage integration.

## Member 3 — Integrity & Evidence

Own:

- SHA-256;
- integrity verification;
- digital signatures (deferred);
- evidence;
- chain of custody.

## Member 4 — Audit & Security Monitoring

Own:

- audit events;
- hash-chained audit log;
- security events;
- failed access tracking;
- alerts;
- audit dashboard data.

## Member 5 — AI/OCR/Search

Own:

- OCR;
- extracted text;
- search;
- AI classification;
- entity extraction;
- summarization;
- AI-assisted search.

## Member 6 — Frontend / QA / Integration

Own:

- dashboard;
- templates;
- navigation;
- document viewer;
- evidence timeline;
- audit UI;
- search UI;
- integration testing;
- demo workflow;
- UI polish.

Member 6 should also act as the primary bug hunter.

---

# 21. AI-Assisted Development Strategy

The team has limited coding experience.

AI therefore becomes a major development tool.

However:

> **AI writes implementation. Humans own requirements, architecture, security decisions and acceptance testing.**

The workflow is:

```text
Requirement
    ↓
AI planning
    ↓
Human review
    ↓
AI implementation
    ↓
Automated tests
    ↓
Human testing
    ↓
Security review
    ↓
Git diff review
    ↓
Commit
```

Never:

```text
"Build the whole app."
```

---

# 22. Antigravity Strategy

Use Antigravity as the primary AI coding environment if it fits the team's available account/access.

The repository should contain:

```text
AGENTS.md
```

and all architecture documents.

AI should read those documents before major changes.

## AI agent roles

### Architect

Reviews:

- architecture;
- dependencies;
- data flow;
- security decisions.

Should not write large amounts of code without approval.

### Django developer

Implements:

- models;
- views;
- forms;
- URLs;
- services;
- tests.

### Security reviewer

Looks for:

- IDOR;
- broken access control;
- CSRF issues;
- XSS;
- SQL injection;
- insecure uploads;
- secret leakage;
- privilege escalation;
- session problems.

### QA agent

Tests:

- valid flows;
- invalid inputs;
- unauthorized users;
- edge cases;
- regression cases.

---

# 23. AI Prompt Rules

Every major AI task should follow:

```text
1. Read project context.
2. Inspect existing code.
3. Plan.
4. Wait for approval for architectural changes.
5. Implement only the requested scope.
6. Run tests.
7. Report changed files.
8. Report failures.
9. Do not silently introduce dependencies.
10. Do not rewrite unrelated code.
```

## Example implementation prompt

```text
Read AGENTS.md and all relevant files in docs/.

Inspect the existing implementation before changing anything.

Implement only the requested feature.

Use existing Django conventions.

Do not introduce a new framework or architecture.

After implementation:

1. Run python manage.py check.
2. Run relevant tests.
3. Run the full test suite where practical.
4. Report changed files.
5. Report dependencies added.
6. Report unresolved issues.

Do not modify unrelated functionality.
```

---

# 24. Git Strategy

Git is mandatory.

## Main branches

```text
main
  │
  └── develop
```

Feature branches:

```text
feature/auth
feature/cases
feature/documents
feature/integrity
feature/audit
feature/ai
feature/ui
```

## Rules

Nobody directly pushes experimental work to `main`.

Before committing:

```bash
git status
git diff
python manage.py check
python manage.py test
```

Then:

```bash
git add .
git commit -m "Implement document versioning"
git push
```

## Commit messages

Good:

```text
Implement custom user model
Add role permissions
Implement case membership checks
Add document versioning
Add SHA-256 integrity verification
Implement audit hash chain
Add OCR processing
```

Bad:

```text
stuff
changes
final
final2
please work
```

---

# 25. Git Recovery Rules

AI can make bad changes.

Git is your parachute.

Before a large AI task:

```bash
git status
git add .
git commit -m "Checkpoint before AI implementation"
```

Then let AI work.

If it destroys the project:

```bash
git diff
```

and restore/revert appropriately.

Do not repeatedly ask an AI agent to fix a mess that it created without understanding the state.

When the codebase becomes confusing:

1. stop;
2. inspect Git history;
3. identify the last known-good commit;
4. restore or branch from it;
5. continue deliberately.

---

# 26. Phase Plan

## Phase 0 — Preparation

**Monday**

Goals:

- repository;
- virtual environment;
- Django;
- SQLite (prototype; PostgreSQL later);
- documentation;
- Git;
- Antigravity.

Deliverables:

```text
GitHub repository
Django skeleton
docs/
AGENTS.md
.env.example
requirements.txt
```

---

# Phase 1 — Authentication Foundation

**Monday**

Start here because every other protected subsystem depends on identity and authorization.

Implement:

- custom User model;
- employee ID;
- department;
- designation;
- account status;
- roles;
- permissions;
- login;
- logout;
- sessions;
- admin management.

Then:

- MFA (deferred);
- password reset;
- rate limiting;
- authorization service;
- IDOR tests;
- security review.

Definition of done:

```text
Admin creates user
       ↓
User logs in
       ↓
MFA (deferred)
       ↓
Dashboard
       ↓
Role restrictions work
       ↓
Unauthorized resource access fails
```

---

# Phase 2 — Case Management

**Tuesday**

Implement:

- case creation;
- case details;
- case status;
- case classification;
- case membership;
- officer assignment;
- authorization tied to cases.

Definition of done:

```text
Officer A
   ↓
Assigned Case
   ↓
Can access

Officer B
   ↓
Not assigned
   ↓
Access denied
```

---

# Phase 3 — Document Management

**Tuesday**

Implement:

- upload;
- metadata;
- categories;
- viewing;
- downloading;
- versioning;
- archival;
- document permissions.

Definition of done:

```text
Case
 ↓
Upload PDF
 ↓
Document appears
 ↓
Version 1
 ↓
Upload new version
 ↓
Version 2
 ↓
History visible
```

---

# Phase 4 — Integrity, Digital Signatures and Evidence

**Tuesday/Wednesday**

Implement:

- SHA-256;
- integrity verification;
- tamper detection;
- digital signatures (deferred);
- evidence registration;
- custody transfers;
- custody timeline.

Definition of done:

```text
Upload
 ↓
Hash
 ↓
Modify file
 ↓
Verify
 ↓
TAMPER DETECTED
```

And:

```text
Evidence
 ↓
Officer A
 ↓
Forensic Officer
 ↓
Court
```

with every transfer recorded.

---

# Phase 5 — Audit & Security Monitoring

**Wednesday**

Implement:

- audit event service;
- audit records;
- hash chaining;
- verification;
- failed access events;
- security dashboard;
- basic suspicious activity detection.

Definition of done:

```text
Action
 ↓
Audit event
 ↓
Hash chain
 ↓
Verify
 ↓
CHAIN VALID
```

And a controlled demo of a modified audit event should show chain failure.

---

# Phase 6 — OCR, Search and AI

**Wednesday**

Implement in this order:

1. OCR;
2. extracted text storage;
3. metadata search;
4. full-text search;
5. AI classification;
6. entity extraction;
7. summarization;
8. natural-language/semantic search if time permits.

Do not begin with an AI chatbot.

The AI must operate on the actual document/case context.

---

# Phase 7 — UI and Integration

**Wednesday**

Build/polish:

- login;
- dashboard;
- cases;
- case details;
- documents;
- document viewer;
- integrity status;
- signatures;
- evidence timeline;
- audit timeline;
- search;
- AI summary;
- security alerts;
- admin.

The UI should make security visible.

---

# Phase 8 — SIH Integration

**Thursday**

No major architectural changes.

Integrate:

```text
Authentication
      ↓
Cases
      ↓
Documents
      ↓
Integrity
      ↓
Audit
      ↓
Evidence
      ↓
Search
      ↓
AI
```

---

# Phase 9 — Testing

**Thursday**

Test the complete workflow.

## Authentication

- valid login;
- invalid login;
- MFA (deferred);
- logout;
- disabled user.

## Authorization

- correct role;
- incorrect role;
- wrong case;
- wrong department;
- classification restriction;
- URL manipulation.

## Documents

- valid upload;
- invalid upload;
- versioning;
- download;
- unauthorized download.

## Integrity

- valid hash;
- modified document;
- invalid signature.

## Evidence

- creation;
- transfer;
- unauthorized transfer;
- custody history.

## Audit

- events generated;
- chain valid;
- chain tampering detected.

## AI

- OCR;
- classification;
- summary;
- malformed AI response;
- API failure.

---

# Phase 10 — Demo and Presentation

**Thursday/Friday**

Do not demo random features.

Tell one story.

## Recommended demo scenario

### Step 1

Admin logs in.

### Step 2

Admin creates an Investigating Officer.

### Step 3

Officer logs in with MFA (deferred).

### Step 4

Officer opens Case CR-2026-00124.

### Step 5

Officer uploads:

```text
FIR.pdf
Forensic_Report.pdf
Witness_Statement.pdf
```

### Step 6

System automatically:

- stores document;
- calculates SHA-256;
- records audit event;
- runs OCR;
- indexes text.

### Step 7

AI produces:

- document classification;
- entities;
- summary.

### Step 8

Officer searches:

```text
Find forensic reports concerning mobile devices.
```

### Step 9

Another officer attempts unauthorized access.

Show:

```text
ACCESS DENIED
```

### Step 10

Show the audit trail.

### Step 11

Modify a document in a controlled demo scenario.

Verify integrity.

Show:

```text
TAMPER DETECTED
```

### Step 12

Show evidence chain:

```text
Officer A
   ↓
Forensic Lab
   ↓
Officer B
   ↓
Court
```

This demonstrates the problem solution rather than a collection of disconnected screens.

---

# 27. Priority System

Not every feature has equal importance.

## P0 — Must work

- authentication;
- authorization;
- cases;
- documents;
- document upload;
- versioning;
- SHA-256;
- audit trail;
- case-based access control.

## P1 — Strong differentiators

- MFA (deferred);
- chain of custody;
- digital signatures (deferred);
- OCR;
- full-text search;
- AI classification;
- AI summary.

## P2 — Nice to have

- semantic search;
- anomaly detection;
- temporary secure sharing;
- blockchain (deferred) anchoring;
- advanced analytics.

If time becomes limited:

**Never sacrifice P0 for P2.**

---

# 28. Blockchain (deferred) Decision

Blockchain (deferred) is optional.

Do not use blockchain (deferred) simply because the problem statement mentions it.

A hash-chained audit log already provides a strong demonstrable tamper-evidence mechanism.

If the core system is complete, a possible extension is:

```text
Audit chain
    ↓
Periodic root hash
    ↓
Blockchain (deferred) anchor
```

The actual documents should not be placed on a public blockchain (deferred).

If blockchain (deferred) consumes time needed for authentication, authorization, document integrity or auditability, remove it.

---

# 29. Encryption Strategy

## In transit

Use HTTPS/TLS.

## At rest

For a stronger implementation, encrypted storage should be used for sensitive files.

For the prototype, do not invent an encryption scheme.

Use established libraries/storage mechanisms.

If application-level encryption is introduced, use authenticated encryption such as AES-GCM through a trusted library and protect keys through environment/secret management.

Never:

```text
key = "mysecret123"
```

inside source code.

---

# 30. File Upload Security

Uploaded documents are untrusted input.

Implement:

- allowed file types;
- size limits;
- filename sanitization;
- safe storage;
- content validation where practical;
- no execution of uploaded files;
- authorization on every retrieval;
- audit logging;
- malware scanning only if feasible and appropriate.

Do not expose arbitrary uploaded files as executable web content.

---

# 31. AI Reliability Rules

AI output can be wrong.

Therefore:

```text
AI suggestion
      ↓
Validation
      ↓
Human review where necessary
      ↓
Stored result
```

Never:

```text
AI
 ↓
Direct database permission update
```

AI should not be trusted to determine authorization.

For legal summaries, label them as AI-generated assistance rather than authoritative legal conclusions.

---

# 32. AI Development Prompt Sequence

For every module use the same sequence.

### Prompt A — Understand

```text
Read AGENTS.md and the relevant project documentation.

Inspect the existing implementation.

Do not modify files.

Explain how the requested feature should fit into the current architecture.
Identify affected models, views, services, templates, URLs and tests.
```

### Prompt B — Plan

```text
Produce a concrete implementation plan.

List:
- files to create/change;
- database changes;
- dependencies;
- security considerations;
- tests.

Do not implement yet.
```

### Prompt C — Implement

```text
Implement only the approved plan.

Do not modify unrelated functionality.

Use existing project conventions.

Run Django checks and relevant tests afterward.
```

### Prompt D — Review

```text
Review the implementation as a senior engineer.

Look for:
- incorrect assumptions;
- security flaws;
- duplicated logic;
- broken authorization;
- unnecessary dependencies;
- migration problems;
- missing tests.

Do not modify files yet.
```

### Prompt E — Fix

```text
Apply only the approved fixes.

Run the complete relevant test suite.

Report changed files and remaining issues.
```

### Prompt F — Commit

Human reviews:

```bash
git diff
python manage.py check
python manage.py test
```

Then commits.

---

# 33. Authentication Prompt Sequence

Authentication is the first actual feature.

## 33.1 Inspect

Ask AI to inspect the current repository and propose the authentication architecture.

## 33.2 Custom User

Implement:

- User;
- employee ID;
- department;
- designation;
- active status.

Do this before creating significant migrations.

## 33.3 Roles

Implement the seven roles.

## 33.4 Permissions

Implement application permissions using Django permissions.

## 33.5 Login/logout

Use Django authentication.

## 33.6 Session security

Configure:

- session cookies;
- HttpOnly;
- SameSite;
- session expiration;
- CSRF;
- HTTPS production settings.

## 33.7 Admin management

Allow administrators to:

- create;
- activate;
- deactivate;
- assign roles;
- assign departments.

## 33.8 MFA (deferred)

Use an established TOTP library.

Do not invent TOTP.

## 33.9 Authorization

Create reusable checks for:

```text
can_user(...)
can_access_case(...)
can_view_document(...)
```

## 33.10 IDOR review

Attack URLs and object IDs deliberately.

## 33.11 Password reset

Use Django's established password-reset framework.

## 33.12 Brute-force protection

Use an established package or carefully implemented throttling.

## 33.13 Security review

Run a dedicated security-agent review.

## 33.14 Tests

Authentication is not complete until tests exist.

---

# 34. Example Authentication Acceptance Test

```text
Admin creates officer
       ↓
Officer activated
       ↓
Officer logs in
       ↓
MFA (deferred) challenge
       ↓
MFA (deferred) succeeds
       ↓
Dashboard
       ↓
Officer accesses assigned case
       ↓
Officer tries another case
       ↓
ACCESS DENIED
       ↓
Admin disables officer
       ↓
Officer tries login
       ↓
LOGIN DENIED
```

---

# 35. Database Development Order

Do not create the entire final database on day one.

Build in dependency order:

```text
1. User
2. Department
3. Roles/Permissions
4. Case
5. CaseMember
6. Document
7. DocumentVersion
8. Evidence
9. CustodyTransfer
10. AuditLog
11. DocumentText
12. AIResult
13. SecurityEvent/Alert
```

Every migration must be tested.

---

# 36. What Can Be Prepared Before the Hackathon

Subject to the hackathon's rules and your institution's interpretation of what pre-development is permitted, prepare the **development foundation** beforehand.

Prepare:

- repository;
- architecture;
- database design;
- documentation;
- environment setup;
- reusable UI shell;
- authentication foundation if permitted;
- test strategy;
- AI prompt templates;
- demo data structure;
- synthetic documents;
- development instructions.

Do not assume that pre-building the actual final submission is permitted.

Check the event rules/instructions applicable to your team.

---

# 37. Three-Day Preparation Plan

## Monday

### Technical setup

- GitHub;
- Django;
- SQLite (prototype; PostgreSQL later);
- virtual environment;
- Antigravity;
- documentation.

### Core architecture

- settings;
- custom user;
- accounts app;
- roles;
- permissions.

### Authentication

- login;
- logout;
- sessions;
- admin user management.

Goal:

> A secure user can log in and reach a protected dashboard.

---

# 38. Tuesday

Morning:

- MFA (deferred);
- password reset;
- rate limiting;
- authorization.

Afternoon:

- cases;
- case membership;
- document model.

Evening:

- upload;
- versions;
- hashes.

Goal:

> A user can securely access an assigned case and its documents.

---

# 39. Wednesday

Morning:

- evidence;
- chain of custody;
- audit;
- hash chain.

Afternoon:

- OCR;
- search;
- AI classification;
- summarization.

Evening:

- UI polish;
- security dashboard;
- integration.

Goal:

> Full demonstrable product flow.

---

# 40. Thursday/Friday

Do not redesign.

Do:

- integrate;
- test;
- fix;
- seed demo data;
- rehearse;
- deploy;
- prepare presentation.

---

# 41. Definition of a Working MVP

The minimum credible system is:

```text
Login
 ↓
Role-based authorization
 ↓
Create case
 ↓
Assign officer
 ↓
Upload document
 ↓
Calculate hash
 ↓
Store version
 ↓
View/download with authorization
 ↓
Audit action
 ↓
Search document
```

If this works reliably, the project already addresses the central problem.

Everything after this makes it stronger.

---

# 42. Definition of the Strong SIH Version

The strong version is:

```text
Authentication + MFA (deferred)
        ↓
RBAC + case-level authorization
        ↓
Case management
        ↓
Secure document storage
        ↓
Version control
        ↓
SHA-256 integrity
        ↓
Digital signature
        ↓
Evidence chain of custody
        ↓
Hash-chained audit trail
        ↓
OCR
        ↓
Full-text search
        ↓
AI classification
        ↓
AI entity extraction
        ↓
AI summarization
        ↓
Security monitoring
```

---

# 43. What We Should NOT Do

Do not:

- build microservices;
- build a React frontend unless necessary;
- build custom cryptography;
- build custom authentication;
- make AI responsible for permissions;
- put documents on a public blockchain (deferred);
- overcomplicate deployment;
- add technologies merely to make the architecture look impressive;
- blindly accept AI-generated code;
- let multiple AI chats independently redesign the database;
- modify migrations casually;
- store secrets in Git.

---

# 44. Common AI Failure Modes

AI may:

### Over-engineer

It may propose:

```text
Django + React + Node + Redis + Kafka + Elasticsearch + Kubernetes
```

Reject this unless there is a real reason.

### Duplicate functionality

It may build its own permission system even though Django already has one.

Reject unnecessary duplication.

### Create insecure CRUD

It may check:

```python
request.user.is_authenticated
```

but forget whether the user is authorized for that specific case/document.

Catch this.

### Trust uploaded files

Reject unsafe file handling.

### Put secrets in source

Never accept this.

### Change unrelated files

Ask it to revert unrelated changes.

### Rewrite working code

Do not allow unnecessary rewrites.

---

# 45. How the Team Should Work With AI

Each teammate should receive:

1. This master document.
2. The current repository.
3. `AGENTS.md`.
4. The specific module documentation.
5. The current Git branch.

They should tell AI:

```text
You are working on SIH26190.

Read the project master documentation and AGENTS.md.

You are responsible only for [MODULE].

Do not redesign the overall architecture.

Inspect existing code before modifying it.

Ask for clarification when requirements conflict.
```

---

# 46. Fresh AI Chat Protocol

When starting a new AI conversation, paste:

```text
You are assisting with SIH26190.

The attached/pasted document is the canonical project specification.

Read it completely before answering.

Do not invent requirements.

Do not change architecture without explicitly explaining why.

The current stack is:

Python
Django
SQLite for the internal prototype; SQLite (prototype; PostgreSQL later) later
Django Templates
HTML/CSS/JavaScript
Gemini/LLM for AI features
Tesseract (deferred) or approved OCR

The project is a secure case-centric legal/investigation document
management system.

The current task is:

[PASTE TASK]

Before coding:
1. Inspect the relevant architecture.
2. Explain the proposed implementation.
3. Identify affected files.
4. Identify security implications.

Do not implement until asked.
```

This should reduce context drift between AI conversations.

---

# 47. Repository Documentation

The repository should eventually contain:

```text
AGENTS.md
README.md

docs/
├── PROJECT_SPEC.md
├── ARCHITECTURE.md
├── DATABASE.md
├── SECURITY.md
├── AI_FEATURES.md
├── UI_SPEC.md
├── TESTING.md
├── DEPLOYMENT.md
└── DEMO_SCRIPT.md
```

`README.md` should contain only the practical setup instructions.

The deeper reasoning belongs in `docs/`.

---

# 48. README Setup

The README should eventually explain:

```text
# SIH26190 DMS

## Requirements

Python 3.14+
SQLite for the internal prototype; SQLite (prototype; PostgreSQL later) later
Git

## Setup

git clone ...
cd ...
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```

Then explain how to run tests.

---

# 49. Demo Data

Never use real police/legal documents.

Create synthetic data:

```text
Case:
CR-2026-00124

Documents:
FIR_CR124.pdf
Forensic_Report_CR124.pdf
Witness_Statement_01.pdf

Evidence:
E-1024
E-1025

Users:
admin@example.local
officer1@example.local
forensic@example.local
auditor@example.local
```

All data should be fictional.

---

# 50. Final Demo Story

The project should tell one coherent story:

> A sensitive investigation case enters the system.

The authorized officer:

1. logs in securely;
2. completes MFA (deferred);
3. accesses the assigned case;
4. uploads a forensic report;
5. the system calculates its integrity hash;
6. OCR extracts its text;
7. AI classifies and summarizes it;
8. the document becomes searchable;
9. another unauthorized officer attempts access and is denied;
10. the audit log records both the legitimate activity and denied attempt;
11. the forensic report is digitally signed;
12. evidence is transferred through a chain of custody;
13. a controlled document modification causes integrity verification to fail;
14. the audit chain remains independently verifiable.

This demonstrates the problem, the solution and the security value in one flow.

---

# 51. Success Criteria

The project is successful if a judge can understand within a few minutes:

### Problem

Sensitive legal documents are fragmented, difficult to retrieve and vulnerable to unauthorized access, tampering and poor auditability.

### Solution

A centralized secure DMS tied to cases and controlled by identity and authorization.

### Differentiation

Every important document has verifiable integrity and a traceable lifecycle.

### Intelligence

AI reduces the manual burden of classification, OCR, extraction, summarization and retrieval.

### Evidence integrity

Versions, hashes, signatures, custody records and audit trails preserve traceability.

---

# 52. Final Architecture

```text
                         USERS
                           │
                           ▼
                    Django Web UI
                           │
                           ▼
                    Authentication
                           │
                    MFA (deferred) + Sessions
                           │
                           ▼
                     Authorization
                    /       |       \
                   /        |        \
                Roles     Cases    Classification
                   \        |        /
                    \       |       /
                     ▼      ▼      ▼
                    Document Management
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           Storage       Hashing       Versioning
              │            │            │
              └────────────┼────────────┘
                           ▼
                         Audit
                           │
                       Hash Chain
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
           Evidence                  Search
              │                         │
        Chain of Custody               OCR
              │                         │
              ▼                         ▼
        Digital Signature              AI
                                      / | \
                              Classification
                              Entities
                              Summary
```

---

# 53. Final Engineering Philosophy

The project is not:

> "Let AI write a website."

The project is:

> **Use AI as an accelerated engineering workforce while the team controls requirements, architecture, security, testing and acceptance.**

Humans decide:

- what the system must do;
- what security guarantees are required;
- what the architecture is;
- whether generated code is acceptable;
- whether tests are meaningful;
- whether the product actually solves the problem.

AI accelerates:

- implementation;
- boilerplate;
- templates;
- tests;
- debugging;
- documentation;
- refactoring;
- UI generation;
- integration work.

---

# 54. Immediate Next Actions

## Member 1 / Technical Lead

1. Create GitHub repository.
2. Create Python virtual environment.
3. Install Django.
4. Install/configure SQLite (prototype; PostgreSQL later).
5. Create Django project.
6. Create `docs/`.
7. Put this master plan in the repository.
8. Create `AGENTS.md`.
9. Commit the initial architecture.
10. Begin authentication.

## Member 2

Begin understanding:

- Django models;
- ORM;
- cases;
- documents;
- file uploads.

## Member 3

Study:

- SHA-256;
- digital signatures (deferred);
- evidence custody;
- Django services.

## Member 4

Study:

- Django signals/services;
- audit logging;
- hash chaining;
- security events.

## Member 5

Study:

- Gemini API;
- OCR;
- prompt design;
- structured AI output;
- document search.

## Member 6

Study:

- Django templates;
- HTML/CSS;
- JavaScript;
- UI workflows;
- testing.

---

# 55. Canonical Rule

Whenever there is uncertainty:

**Do not ask "What would be the coolest technology?"**

Ask:

> "What is the simplest secure implementation that demonstrably solves the SIH26190 requirement?"

That is the guiding principle of this project.

---

# Sources and Reference Notes

The SIH26190 title, organization and core background/description were cross-checked against indexed 2026 SIH problem-statement archives and mirrors.

Primary reference to verify against the current SIH portal:
https://www.sih.gov.in/

Indexed problem statement archive:
https://github.com/NoBugNinja/Smart-India-Hackathon-SIH-2026-Problem-Statements

SIH 2026 Explorer:
https://sih-explorer.amanuniyal47.workers.dev/problem/SIH26190

Django documentation:
https://docs.djangoproject.com/

The project team should prefer the current official SIH portal and official framework documentation over third-party summaries when requirements or technical behavior are disputed.
