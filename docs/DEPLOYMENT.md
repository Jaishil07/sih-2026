# DEPLOYMENT.md

## Prototype
Local development is the priority.

Use SQLite.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Windows:
```powershell
.venv\Scripts\Activate.ps1
```

## Environment
`.env`:
```text
DJANGO_SECRET_KEY=...
DEBUG=True
GEMINI_API_KEY=...
```

Never commit `.env`.

## Later
Production may use PostgreSQL, HTTPS, secret management, object storage and production Django settings. None are internal-round P0.
