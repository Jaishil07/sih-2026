# AGENTS.md

## Project
SIH26190 Secure Digital Document and Evidence Management System.

## Read First
- docs/PROJECT_MASTER.md
- docs/PROJECT_SPEC.md
- docs/ARCHITECTURE.md
- docs/DATABASE.md
- docs/SECURITY.md
- docs/AI_FEATURES.md
- docs/UI_SPEC.md
- docs/TESTING.md

## Stack
Python + Django + SQLite + Django Templates + HTML/CSS/JavaScript + Gemini/approved LLM.

## Prototype Constraints
Do not introduce without technical-lead approval:
- React
- Node backend
- microservices
- Kubernetes
- PostgreSQL
- MFA/TOTP
- Tesseract
- PKI/digital signatures
- blockchain

## Development Process
1. Inspect existing code.
2. Identify affected files.
3. Explain the plan.
4. Identify DB changes.
5. Identify security implications.
6. Implement only approved scope.
7. Run `python manage.py check`.
8. Run tests.
9. Report changed files and unresolved issues.

## Security
Never hard-code secrets, store plaintext passwords, bypass authorization, disable CSRF casually, trust uploads or expose private documents.

AI cannot control authorization.

## Database
Use Django ORM. Use SQLite. Do not write SQLite-specific SQL. Do not casually rewrite shared migrations.

## Git
Do not commit automatically unless asked. Do not push directly to main. Create a checkpoint before large AI changes.

## Scope
If a feature is not in the current task, do not implement it.
