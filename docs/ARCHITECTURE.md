# ARCHITECTURE.md

## Architecture Decision
Use a modular Django monolith.

## Stack
- Python
- Django
- SQLite
- Django Templates
- HTML/CSS/JavaScript
- Bootstrap CDN or simple CSS
- Gemini/approved LLM
- pypdf/pdfplumber
- Django media storage

## Apps
```text
apps/
├── accounts/
├── cases/
├── documents/
├── evidence/
├── audit/
└── ai_assistant/
```

## Request Flow
```text
Browser → URL → View → Authentication → Authorization
→ Service/business logic → Model/storage → Audit → Response
```

## Upload Flow
```text
Upload → Validate → Authorize → Store → SHA-256
→ DocumentVersion → Audit → AI/text extraction
```

## Rules
- Keep views thin.
- Prefer Django built-ins.
- Use Django ORM.
- Do not introduce microservices.
- Do not introduce React for the prototype.
- Do not require PostgreSQL for the prototype.
- AI never controls authorization.
