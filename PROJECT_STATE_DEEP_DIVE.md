# PROJECT_STATE_DEEP_DIVE.md

## SECTION 1: PROJECT IDENTITY & METADATA
- **Project Name & Codename:** Suraksha Docs / Suraksha DMS / sih-2026
- **Origin Context:** Hackathon project built during the 36-hour Smart India Hackathon (SIH 2026) internal hackathon on September 10–11, 2026 at Karnavati University.
- **Problem Statement ID:** PS 26190 (Digital Evidence Management & Chain of Custody System).
- **Primary Legal & Compliance Alignment:** Bharatiya Sakshya Adhiniyam (BSA) Section 63 / Indian Evidence Act Section 65B compliance for electronic record admissibility.
- **System Purpose:** A national secure legal and investigation document repository (Suraksha Docs) designed to manage digital evidence and maintain an immutable chain of custody for law enforcement agencies, ensuring cryptographic integrity and secure role-based access to legal documents and cases.

---

## SECTION 2: FULL REPOSITORY & FILE INVENTORY
The repository is structured around a central Django project with modularized apps.

- **Project Root Files:**
  - `manage.py`: Django’s command-line utility for administrative tasks.
  - `.env`: Environment variables file (stores `SECRET_KEY`, `DEBUG`, `GEMINI_API_KEY`).
  - `.gitignore`: Git exclusions.
  - `README.md` & `PROJECT_MASTER.md`: Documentation files.
  - `requirements.txt`: Python package dependencies.
  - `db.sqlite3`: The local SQLite runtime database file.

- **Virtual Environment (`venv/`):** Standard Python virtual environment housing all dependencies.

- **Project Configuration (`config/`):**
  - `settings.py`: Core Django settings, database configuration, middleware, and installed apps.
  - `urls.py`: Master URL routing, including all application routes.
  - `wsgi.py` / `asgi.py`: WSGI/ASGI entry points for production web servers.

- **Django Applications (`apps/`):**
  - `accounts/`: User identity, authentication, MFA configuration, and RBAC utilities (`models.py`, `views.py`, `urls.py`, `services.py`).
  - `audit/`: Global audit logging and tamper-evident event chains (`models.py`, `views.py`, `urls.py`, `services.py`).
  - `blockchain/`: Internal Proof-of-Work blockchain for anchoring document hashes and audit events (`models.py`, `views.py`, `urls.py`, `services.py`).
  - `cases/`: Management of investigation cases, case members, persons of interest, and case notes (`models.py`, `views.py`, `urls.py`).
  - `documents/`: Legal document upload, dynamic versioning, AI extraction integration, and digital signatures (`models.py`, `views.py`, `urls.py`, `services.py`, `forms.py`).
  - `evidence/`: Physical and digital evidence tracking, approval workflows, and chain of custody transfers (`models.py`, `views.py`, `urls.py`).
  - `ai_assistant/`: AI processing models (document text extraction, AI results) and global search implementations (`models.py`, `views.py`, `urls.py`, `services.py`).

- **Static and Media Assets:**
  - `static/`: Source static files (custom CSS, JS).
  - `staticfiles/`: Target directory for `collectstatic`, served by Nginx in production.
  - `media/`: Storage location for user-uploaded documents and evidence.
  - `templates/`: Global Django HTML templates (e.g., `base.html`, `dashboard.html` and app-specific template folders).

- **Deployment (`deploy/`):**
  - `setup.sh`: Automated bash script for EC2 instance provisioning, package installs, and service setup.
  - `update.sh`: Script to pull latest code, run migrations, and restart services.
  - `gunicorn.service`: Systemd service unit for managing the Gunicorn daemon.
  - `nginx.conf`: Nginx virtual host configuration.

---

## SECTION 3: TECH STACK & PRODUCTION INFRASTRUCTURE
- **Programming Language & Core Framework:** Python 3 (implicitly via Ubuntu 24.04 and venv) running Django 6.1.1.
- **WSGI & Web Server:** 
  - **Gunicorn:** Runs via a systemd unit (`/etc/systemd/system/gunicorn.service`) using 3 worker processes. Binds to a unix socket at `/home/ubuntu/sih-2026/gunicorn.sock`. Runs under the `ubuntu` user and `www-data` group.
  - **Nginx:** Acts as a reverse-proxy (listening on port 80/443). Passes traffic to the Gunicorn socket. Configured to allow large file uploads (`client_max_body_size 50M`) and serves static (`/home/ubuntu/sih-2026/staticfiles/`) and media files (`/home/ubuntu/sih-2026/media/`) directly via aliases.
- **Database Engine:** SQLite runtime (`db.sqlite3`). Configured natively in `settings.py`. Production requires file ownership to be `ubuntu:www-data` and permissions to be `664` on the file and `775` on the parent directory to prevent write locks during concurrent access.
- **Cryptography & Security:**
  - Standard SHA-256 implemented via `hashlib` in Python for file hashing and blockchain mining.
  - `cryptography.hazmat` utilized for generating ephemeral RSA 2048-bit key pairs and applying RSA-PSS-SHA256 signatures for document locking.
  - Expected Let's Encrypt / Certbot TLS configuration at the Nginx layer for HTTPS.
- **Hosting Environment:** AWS EC2 instance running Ubuntu 24.04 LTS. Configured with a 2GB swap file. Domain mapped dynamically using DuckDNS (`suraksha-dms.duckdns.org` -> AWS public IP).

---

## SECTION 4: AUTHENTICATION, AUTHORIZATION & RBAC
- **User Model Implementation:** A custom user model (`apps.accounts.models.User`) extending `django.contrib.auth.models.AbstractUser`. Adds custom fields: `employee_id`, `role`, `department`, `designation`, `supervisor`, `mfa_enabled`, and `mfa_secret`. Configured via `AUTH_USER_MODEL = "accounts.User"`.
- **User Roles & Tiers:**
  - `ADMIN`
  - `SENIOR_OFFICER`
  - `INVESTIGATING_OFFICER`
  - `FORENSIC_OFFICER`
  - `PROSECUTOR`
  - `COURT_USER`
  - `AUDITOR`
- **Role Assignment & Permission Checks:** 
  - Authorization is verified using service methods in `apps.accounts.services` (e.g., `can_access_case`, `can_upload_document`).
  - View access is guarded by Django’s `@login_required` decorator for function-based views and `LoginRequiredMixin` for class-based views. Explicit role logic dictates queryset filtering (e.g. Admins see all cases, Investigators only see assigned ones).
- **Session Architecture:** 
  - Django’s default `SessionMiddleware` and `AuthenticationMiddleware`.
  - CSRF protections enforced via `CsrfViewMiddleware` with `CSRF_TRUSTED_ORIGINS` mapped to `http://*.compute.amazonaws.com` (configurable via `.env`).
  - `SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"` applied for preview station compatibility.
  - Optional TOTP-based Multi-Factor Authentication (MFA) provided by the `pyotp` library.

---

## SECTION 5: DATA SCHEMA & MODEL RELATIONSHIPS

### App: `accounts`
- **`User` (table: `accounts_user`)**: Extends `AbstractUser`. Purpose: System identity.
  - Fields: `employee_id` (CharField, unique), `role` (CharField, choices), `department` (CharField), `designation` (CharField), `supervisor` (ForeignKey to `self`, SET_NULL), `mfa_enabled` (BooleanField), `mfa_secret` (CharField).

### App: `cases`
- **`Case` (table: `cases_case`)**: Core case container.
  - Fields: `case_number` (CharField, unique), `title`, `description`, `status` (default="OPEN"), `classification`, `created_by` (FK to User, SET_NULL), `created_at`, `updated_at`.
- **`CaseMember` (table: `cases_casemember`)**: Maps Users to Cases with specific roles.
  - Fields: `case` (FK to Case), `user` (FK to User), `role` (CharField), `assigned_at`. `unique_together` constraint on (`case`, `user`).
- **`PersonOfInterest` (table: `cases_personofinterest`)**: Suspects, victims, witnesses linked to a case.
  - Fields: `case` (FK to Case), `name`, `alias`, `role_in_case` (choices), `identification_number`, `notes`, `created_at`.
- **`CaseNote` (table: `cases_casenote`)**: Textual notes attached to a case.
  - Fields: `case` (FK to Case), `author` (FK to User), `content`, `created_at`. Ordered by `-created_at`.

### App: `documents`
- **`Document` (table: `documents_document`)**: Logical container for uploaded legal documents.
  - Fields: `case` (FK to Case), `title`, `document_type` (choices), `classification` (choices), `status` (default="ACTIVE"), `created_by` (FK to User), `created_at`, `updated_at`, `is_locked` (BooleanField), `locked_at`, `locked_by` (FK to User, SET_NULL).
- **`DocumentVersion` (table: `documents_documentversion`)**: Physical file revisions of a Document.
  - Fields: `document` (FK to Document), `version_number` (PositiveIntegerField), `file` (FileField, `upload_to="documents/%Y/%m/"`), `sha256_hash` (CharField), `change_reason`, `is_signed` (BooleanField), `created_by` (FK to User), `created_at`.
- **`DocumentSignature` (table: `documents_documentsignature`)**: Cryptographic signatures locking a document version.
  - Fields: `version` (OneToOneField to DocumentVersion), `signer` (FK to User, PROTECT), `certificate_id` (CharField, unique), `signature_hex` (TextField), `public_key_pem` (TextField), `signed_at`, `algorithm` (default="RSA-PSS-SHA256").

### App: `evidence`
- **`Evidence` (table: `evidence_evidence`)**: Physical or digital evidence records.
  - Fields: `case` (FK to Case), `evidence_number` (CharField, unique), `description`, `current_custodian` (FK to User, SET_NULL), `status` (choices), `approved_by` (FK to User, SET_NULL), `approval_notes`, `approved_at`, `created_at`.
- **`CustodyTransfer` (table: `evidence_custodytransfer`)**: Immutable chain of custody handoffs.
  - Fields: `evidence` (FK to Evidence), `from_user` (FK to User, SET_NULL), `to_user` (FK to User, SET_NULL), `reason`, `location`, `status` (PENDING/ACCEPTED/REJECTED), `timestamp`, `accepted_at`, `rejection_reason`.

### App: `audit`
- **`AuditLog` (table: `audit_auditlog`)**: System-wide action ledger.
  - Fields: `actor` (FK to User, SET_NULL), `action` (CharField), `resource_type`, `resource_id`, `ip_address`, `details` (JSONField), `previous_hash` (CharField), `event_hash` (CharField), `timestamp`.

### App: `blockchain`
- **`Block` (table: `blockchain_block`)**: Proof-of-Work blockchain nodes.
  - Fields: `index` (PositiveIntegerField, unique), `timestamp`, `transactions` (JSONField), `previous_hash` (CharField), `block_hash` (CharField, unique), `nonce` (PositiveIntegerField), `merkle_root`.

### App: `ai_assistant`
- **`DocumentText` & `AIResult`**: Extracted OCR/metadata and AI generation summaries tied to `Document`.

---

## SECTION 6: EVIDENCE INGESTION & HASH INTEGRITY PIPELINE
- **Intake Flow:** Users upload files via the `DocumentUploadForm` targeting `views.document_upload_view`. The Nginx reverse proxy accepts payloads up to 50MB (`client_max_body_size`).
- **Cryptographic Hashing:** During `services.create_document_version()`, the system intercepts the raw file stream before disk serialization. It utilizes `hashlib.sha256()`, reading the file buffer in 64KB chunks to compute the hash (`calculate_sha256()`).
- **Storage Strategy:** The file is persisted to disk under `/media/documents/YYYY/MM/` as defined by the `FileField`'s `upload_to` parameter. Duplicate filenames are sanitized natively by Django's storage backend (appending hashes/strings).
- **WORM (Write Once, Read Many) Enforcements:**
  - Files cannot be overwritten; new uploads create incremental `DocumentVersion` entities.
  - Files cannot be deleted; the `document_delete_view` only sets `Document.status = 'ARCHIVED'` (Soft-delete).
  - True lock enforcement: A user invokes `document_sign_view`, triggering a digital RSA signature. This toggles `Document.is_locked = True`. Any subsequent attempt to call `create_document_version` raises a `PermissionDenied("Document is permanently locked.")`.

---

## SECTION 7: BLOCKCHAIN & AUDIT TRAIL IMPLEMENTATION
- **Ledger Architecture:** A synchronous Python-based Proof-of-Work local blockchain stored in the relational database (`Block` table).
- **Block Structure:**
  - `index`: Monotonically increasing integer.
  - `timestamp`: UTC ISO-8601 representation.
  - `transactions`: JSON payload array (e.g. `{"type": "DOCUMENT_ANCHOR", "sha256_hash": "...", ...}`).
  - `previous_hash`: The SHA-256 output of the parent block.
  - `nonce`: Proof-of-Work counter to satisfy the difficulty prefix (e.g., `00`).
  - `block_hash`: The verified hash output locking the block.
- **Tamper Verification Logic:** 
  The `verify_blockchain_integrity()` function iterates over all blocks ordered by `index`. It rebuilds the string format `index|timestamp|transactions_json|previous_hash|nonce`, computes the SHA-256, and compares it to the stored `block_hash`. It also validates that the current block's `previous_hash` matches the preceding block's `block_hash`. Any deviation flags the block as tampered.
- **Audit Logging:** The `AuditLog` model mirrors this approach, storing an `event_hash` and `previous_hash` to create a secondary cryptographic chain specifically for user actions, verifiable via `verify_audit_chain()`. Immutability relies on application logic restricting UPDATE/DELETE interfaces.

---

## SECTION 8: FULL URL ROUTING & VIEW CONTROLLER DIRECTORY

### Root Configurations (`config/urls.py`)
- `/admin/`: Django Admin Interface.
- `/accounts/login/`: `CustomLoginView` -> Logs users in.
- `/accounts/logout/`: `CustomLogoutView` -> Logs users out.
- `/`: `DashboardView` -> Base system dashboard (`GET`).

### Accounts (`apps/accounts/urls.py`)
- `/accounts/users/`: `UserListView` (`GET`).
- `/accounts/users/create/`: `UserCreateView` (`GET`, `POST`).
- `/accounts/users/<id>/deactivate/`: `UserDeactivateView` (`POST`).
- `/accounts/users/<id>/update-supervisor/`: `UserUpdateSupervisorView` (`POST`).
- `/accounts/password-change/`: `CustomPasswordChangeView` (`GET`, `POST`).
- `/accounts/profile/`: `ProfileView` (`GET`).
- `/accounts/mfa/verify/`: `MfaVerifyView` (`GET`, `POST`).
- `/accounts/mfa/setup/`: `MfaSetupView` (`GET`, `POST`).

### Cases (`apps/cases/urls.py`)
- `/cases/`: `CaseListView` (`GET`).
- `/cases/new/`: `CaseCreateView` (`GET`, `POST`).
- `/cases/<id>/`: `case_detail_view` (`GET`).
- `/cases/<id>/poi/add/`: `add_person_of_interest_view` (`POST`).
- `/cases/<id>/members/assign/`: `assign_member_view` (`POST`).
- `/cases/<id>/notes/add/`: `add_case_note_view` (`POST`).
- `/cases/<id>/close/`: `CaseCloseView` (`POST`).
- `/cases/<id>/reopen/`: `CaseReopenView` (`POST`).

### Documents (`apps/documents/urls.py`)
- `/documents/`: `DocumentListView` (`GET`).
- `/documents/case/<id>/upload/`: `document_upload_view` (`GET`, `POST`). Uploads file and initiates AI analysis.
- `/documents/<id>/`: `document_detail_view` (`GET`, `POST`). Shows file, versions, hash verification, allows new version upload.
- `/documents/<id>/delete/`: `document_delete_view` (`POST`). Soft deletes/archives document.
- `/documents/<id>/preview/`: `document_preview_view` (`GET`). Secure inline file rendering.
- `/documents/<id>/sign/`: `document_sign_view` (`POST`). Applies RSA signature and locks document.
- `/documents/version/<id>/download/`: `document_download_view` (`GET`). Serves the raw file attachment.

### Evidence (`apps/evidence/urls.py`)
- `/evidence/`: `EvidenceListView` (`GET`).
- `/evidence/case/<id>/add/`: `evidence_create_view` (`GET`, `POST`).
- `/evidence/<id>/`: `evidence_detail_view` (`GET`, `POST`).
- `/evidence/<id>/transfer/`: `transfer_custody_view` (`POST`). Initiates chain of custody handoff.
- `/evidence/<id>/approve/`: `approve_evidence_view` (`POST`).
- `/evidence/transfer/<id>/accept/`: `accept_custody_transfer_view` (`POST`). Approves pending handoff.
- `/evidence/transfer/<id>/reject/`: `reject_custody_transfer_view` (`POST`). Rejects pending handoff.

### Audit & Blockchain & Search
- `/audit/`: `AuditListView` (`GET`).
- `/audit/verify/`: `verify_audit_chain_view` (`GET`). Recalculates cryptographic audit chain.
- `/blockchain/`: `blockchain_explorer_view` (`GET`). Views and verifies internal blockchain states.
- `/search/`: `global_search_view` (`GET`). Scans documents, evidence, POIs, and notes.

---

## SECTION 9: FRONTEND, UI COMPONENTS & TEMPLATES
- **Rendering Engine:** Standard Django Template Language (DTL) extending from `templates/base.html`.
- **Styling & Assets:** 
  - Framework: Bootstrap 5.3.2 (via CDN).
  - Icons: Bootstrap Icons.
  - Typography: Google Fonts (Inter).
  - Custom CSS: `static/css/custom.css`.
- **Client-Side Scripting:** 
  - Theme toggling system switching `data-bs-theme` between `light` and `dark` modes, persisted in `localStorage`.
  - Vanilla JS for 5-second automatic dismissal of floating Bootstrap alert messages.

---

## SECTION 10: DEPLOYMENT, ENVIRONMENT & DEV-OPS HISTORY
- **Environment Variables (`.env`):**
  - `DJANGO_SECRET_KEY`: `sih-hackathon-demo-key-secret-2026!`
  - `DEBUG`: `True`
  - `GEMINI_API_KEY`: (Blank)
- **Systemd Service Unit (`gunicorn.service`):**
  Executes `/home/ubuntu/sih-2026/venv/bin/gunicorn` under `User=ubuntu` and `Group=www-data`. Binds to `unix:/home/ubuntu/sih-2026/gunicorn.sock` with 3 workers.
- **Nginx Configuration (`nginx.conf`):**
  Listens on port 80. Sets `client_max_body_size 50M`. Defines location blocks mapping `/static/` to `staticfiles/` and `/media/` to `media/`, proxying all other traffic to `http://unix:/home/ubuntu/sih-2026/gunicorn.sock`.
- **Historical Fixes Applied During Deployment:**
  - **Nginx 502 Bad Gateway:** Fixed by assigning `ubuntu:www-data` ownership to the `/home/ubuntu/sih-2026` directory and modifying folder permissions to `755` so Nginx (`www-data`) could access the gunicorn socket.
  - **SQLite Write Locks:** Fixed by applying file mode `664` to `db.sqlite3` and `775` to the project directory, allowing both Gunicorn workers and the web server write access.
  - **Django `ImproperlyConfigured`:** Mitigated by creating the `.env` file for `SECRET_KEY` and implementing Python-dotenv loads in `settings.py`.
  - **`ALLOWED_HOSTS` Syntax Error:** Corrected by converting comma-separated strings from `os.environ.get()` into pure Python lists via `.split(",")`.
  - **Certbot SSL Installation:** Implicitly bound to `suraksha-dms.duckdns.org` facilitating secure connections.

---

## SECTION 11: SYSTEM LIMITATIONS & JURY ROADMAP DEFENSE
- **Current Prototype Vulnerabilities:**
  - SQLite concurrency bottlenecks under high concurrent write loads (Audit logs, Blockchain mining).
  - Direct server-side media storage on EBS root volumes restricts horizontal scalability.
  - Lack of hardware-backed mobile signing (relying on server-generated ephemeral RSA keys).
- **Architectural Mitigation Roadmap:**
  - **Database Migration:** Upgrade to PostgreSQL 16 with connection pooling (PgBouncer) for production deployment.
  - **Object Storage:** AWS S3 / MinIO integration using signed pre-shared URLs to offload high-volume evidence uploads from application servers.
  - **Hardware Integrity:** C2PA (Coalition for Content Provenance and Authenticity) integration directly into mobile camera intake to cryptographically prove photo provenance at capture.
  - **Compliance:** Implement cryptographic shredding (deletion of encryption keys instead of physical file erasure) to ensure data retention compliance under India's Digital Personal Data Protection (DPDP) Act.
