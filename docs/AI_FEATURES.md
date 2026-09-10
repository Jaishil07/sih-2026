# AI_FEATURES.md

## Philosophy
AI assists users. It does not control security.

## Classification
Suggest a document type from text and metadata.

## Entity Extraction
Extract:
- people
- organizations
- locations
- dates
- case numbers
- evidence IDs

## Summary
Generate:
- short summary
- key findings
- important dates
- referenced evidence

## Search Assistance
Support natural-language queries such as:
> Find forensic reports related to mobile devices.

The AI may interpret a query, but deterministic authorization controls which documents can be returned.

## First Prototype
```text
sample text/PDF
 ↓
Python script
 ↓
Gemini
 ↓
structured JSON
```

Integrate into Django only after the standalone proof of concept works.

## Failure Handling
Handle missing keys, API errors, timeouts, malformed JSON and rate limits.

AI failure must not crash the DMS.

## Deferred
Vector databases, complex agents and chatbots are optional.
