# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

AI EMR (AI Electronic Medical Records) — a Django REST API backend for AI-powered medical transcription and analysis. Backend only; frontend is deployed separately and not in this repo.

### Running the dev server

Always use the dev settings module for local development:

```
source venv/bin/activate
DJANGO_SETTINGS_MODULE=backend.settings_dev python manage.py runserver 0.0.0.0:8000
```

`backend/settings_dev.py` overrides the production settings to use SQLite (instead of MySQL), `DEBUG=True`, `localhost` in `ALLOWED_HOSTS`, and disables secure cookies. The production `settings.py` has hardcoded MySQL credentials and is not suitable for local development.

### Environment variables

A `.env` file in the project root is required (loaded by `python-decouple`). Required keys: `SECRET_KEY`, `OPENAI_API_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`. For local dev, set `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` to avoid needing real SMTP credentials.

### Running tests

```
source venv/bin/activate
DJANGO_SETTINGS_MODULE=backend.settings_dev python manage.py test
```

Note: test files (`auth_app/tests.py`, `med_app/tests.py`) are currently empty stubs.

### System checks

```
DJANGO_SETTINGS_MODULE=backend.settings_dev python manage.py check
```

### Key API endpoints

- Auth: `/api/auth/login/`, `/api/auth/register/`, `/api/auth/logout/`
- Medical: `/api/med/transcripts/`, `/api/med/analyses/`, `/api/med/all-chats/`, `/api/med/analyze-transcript/`
- Admin: `/admin/`

### Gotchas

- The `OPENAI_API_KEY` in `.env` must be a valid OpenAI key for the `/api/med/analyze-transcript/` endpoint to work. Other endpoints work with a placeholder.
- Migrations must be run with `DJANGO_SETTINGS_MODULE=backend.settings_dev` to target SQLite.
- The `mysqlclient` pip package requires system packages `default-libmysqlclient-dev`, `pkg-config`, and `python3.12-dev` to compile.
