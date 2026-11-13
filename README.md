# FinTrack — Personal Finance App

FinTrack is a Flask personal-finance web application created as a CS50 final project. It provides account management and tools for organizing transactions, budgets, and savings goals.

## Features

- Register and sign in with a username and password
- Email verification and password-reset flows (SMTP configuration required)
- Optional Google OAuth sign-in (OAuth credentials required)
- Create and manage income and expense transactions, including currency conversion
- Create budgets with weekly, monthly, or yearly periods
- Create savings goals and track contributions
- Manage categories and user preferences, including theme and preferred currency
- View dashboard summaries and charts
- Export financial data as CSV and PDF

External integrations such as SMTP, Google OAuth, and the CurrencyLayer API require credentials. Without an exchange-rate API key, the app can use its fallback rates.

## Requirements

- Python 3
- Dependencies listed in `requirements.txt`
- Optional test dependencies in `requirements-test.txt`

## Installation and setup

```bash
git clone https://github.com/Derdev74/CS50-Final-Project.git
cd CS50-Final-Project

python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional: install test dependencies
pip install -r requirements-test.txt

# Create a local environment file from the example, then edit its values
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env

flask --app app run
```

Set a unique, randomly generated `SECRET_KEY` in `.env`. Configure `MAIL_*` values for email workflows. Google OAuth and CurrencyLayer settings are optional and are only needed for those integrations. Do not commit `.env` or real credentials.

The app stores its SQLite database under `instance/` and file-based sessions under `flask_session/`. These are generated runtime data and are intentionally excluded from Git. The database is initialized by the application when it starts.

## Running tests

```bash
pytest -v
pytest --cov
pytest tests/test_auth.py
```

## Project layout

- `app.py` — Flask application and routes
- `helpers.py` — shared helpers and currency service
- `services.py` — authentication and user services
- `export_service.py` — CSV and PDF exports
- `oauth_service.py` — Google OAuth integration
- `templates/` — Jinja templates, including email templates
- `static/` — CSS and JavaScript assets
- `tests/` — pytest test modules

## Configuration and security notes

Use `.env.example` as a template only; its values are placeholders, not credentials. Keep local databases, session files, logs, and `.env` files private. This project is an educational CS50 submission and is not represented as a production-ready financial service.

## Acknowledgments

Built with Flask, SQLite, the CS50 SQL library, and the open-source projects listed in `requirements.txt`. Created as a CS50 final project; follow the course's academic-integrity requirements when referencing or reusing the work.
