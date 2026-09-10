# SECURITY.md

## Prototype Goal
Demonstrate meaningful secure design without pretending the internal prototype is a production government system.

## Authentication
Use Django authentication. Do not implement custom password hashing. MFA is deferred.

## Authorization
Authentication is not authorization.

Minimum:
```text
Authenticated?
 ↓
Role?
 ↓
Case membership?
 ↓
Document permission?
 ↓
Action
```

## IDOR
Never return a resource merely because the user knows its ID. Authorization must be checked against the actual object.

## Uploads
- restrict types
- limit size
- sanitize filenames
- safe media storage
- never execute uploads
- authorize downloads

## Integrity
Hash actual file bytes with SHA-256.

## Audit
Important actions create events. Events form a hash chain.

## Secrets
Never commit `.env`, API keys, Django secret keys or passwords.

## AI
AI cannot authorize, change permissions, delete evidence, modify audit records or make legal decisions.

## Deferred Hardening
MFA, password reset, rate limiting, SSO, PKI, production key management and advanced malware scanning.
