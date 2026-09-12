# Suraksha Docs (Suraksha DMS)

A secure, tamper-evident **Digital Evidence Management and Chain of Custody System** engineered for law enforcement agencies, forensic examiners, and corporate compliance units. 

Suraksha Docs guarantees evidentiary integrity from the point of ingestion to courtroom presentation, ensuring verifiable compliance with modern electronic admissibility frameworks (including **Section 63 of the Bharatiya Sakshya Adhiniyam** / Section 65B Indian Evidence Act).

---

## Key Capabilities

* **Cryptographic Evidence Ingestion:** Computes client-verified **SHA-256** checksums upon file ingestion, ensuring any post-upload alteration is immediately detected.
* **Immutable Audit Trails:** Employs an append-only event-sourcing model where every action—case creation, viewing, reassignment, and status transition—is permanently logged.
* **WORM (Write Once, Read Many) File Versioning:** Uploaded digital artifacts cannot be deleted or overwritten by any user or administrator; subsequent revisions create strict child version artifacts with linked checksums.
* **Strict Separation of Duties:** Distinct administrative layers separate infrastructural management (IT Cell) from case management and evidence approval (Investigating Officers and Supervisory Admins).
* **Legal Dossier Export:** Generates standardized, offline-verifiable case manifests and certificates of electronic evidence for submission to courts or arbitration tribunals.

---

## Target Users & Operational Roles

| Role | Responsibilities | Permissions & Controls |
|---|---|---|
| **Investigating Officer (IO)** | First responder, case registration, evidence intake | Creates cases, attaches POIs (Persons of Interest), uploads initial evidence. |
| **Evidence Custodian (*Malkhana*)** | Custody verification, warehouse transfers | Verifies handoffs, logs physical/digital custody transfers. |
| **Supervisory Officer (SHO / SP)** | Case review, reassignment, final sign-off | Reviews locked files, approves transfers; subject to Dual-Authorization controls. |
| **System Admin (IT Cell)** | User provisioning, server infrastructure | Manages user accounts and system configuration; **zero** direct case-modification access. |
| **Auditor / Legal Counsel** | Court presentation, forensic cross-examination | Read-only access to immutable audit trails, hash manifests, and verification tools. |

---

## Technology Stack

* **Backend Framework:** Python 3.14+, Django 5.x
* **WSGI Application Server:** Gunicorn 26.x
* **Reverse Proxy & Web Server:** Nginx
* **Database:** SQLite 3 (configured with WAL and restricted file permissions)
* **Security & Encryption:** Certbot (Let's Encrypt TLS/SSL), SHA-256 Cryptographic Hashing
* **Cloud Infrastructure:** AWS EC2 (Ubuntu 24.04 LTS)
* **Domain Resolution:** Dynamic DNS (`suraksha-dms.duckdns.org`)

---

## Local Development Setup

### 1. Prerequisites
* Python 3.11+
* Git
* OpenSSL

### 2. Clone the Repository
```bash
git clone https://github.com/Jaishil07/sih-2026.git 
cd sih-2026
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```