# UI_SPEC.md

## Goal
Simple, coherent and demo-friendly.

## Layout
```text
Header
├── Dashboard
├── Cases
├── Documents
├── Evidence
├── Search
└── Audit
```

Use Django Templates and Bootstrap CDN or simple CSS.

## Pages

### Login
- employee ID/email
- password

### Dashboard
- active cases
- documents
- recent activity
- alerts

### Case
- case number
- title
- status
- classification
- assigned users
- documents
- evidence

### Document
- title
- type
- classification
- version
- SHA-256
- integrity status
- AI summary
- audit history

### Evidence
- evidence ID
- description
- current custodian
- custody timeline

### Audit
- timestamp
- actor
- action
- resource
- status
- chain status

### Search
- case
- document type
- title
- extracted text

Make security visible:
`✓ Integrity Verified`
`ACCESS DENIED`
`✓ Audit Chain Valid`
`⚠ TAMPER DETECTED`
