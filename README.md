# Demo Linux Server Monitoring

Local Flask demo for viewing Linux CPU, memory, network, and listening ports over SSH — without logging into each host.

Specs: [docs/requirements.md](docs/requirements.md) · Tasks: [docs/TODO.md](docs/TODO.md) · Usage: [docs/usage.md](docs/usage.md)

## Quick start

```bash
cd monitoring_application
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**

Or with Flask CLI:

```bash
export FLASK_APP=app.py
flask run --host=127.0.0.1 --port=5000
```

### Default login

| Field | Value |
|-------|--------|
| Username | `admin` |
| Password | `admin123` (stored **hashed** in SQLite) |

### Configuration

Copy `.env.example` ideas into your shell (do not commit `.env`):

```bash
export SECRET_KEY="your-local-secret"
# Optional: DEMO_AUTO_TRUST_SSH=1  (default for demo host-key policy)
```

- **SECRET_KEY** — signs the session cookie. Change for anything beyond a laptop demo.
- **Database** — SQLite file at `instance/monitoring.db` (gitignored). Created on first run.

## Features

- Single admin session (Flask signed cookie)
- Add / edit / delete Linux servers (SSH password or private key)
- Collect CPU, memory, network, ports every **5 minutes** (+ manual refresh)
- Read-only metrics UI; CSRF on mutating forms

## SSH notes (demo)

- Auth: password **or** PEM private key
- Host keys: demo default uses AutoAddPolicy when `DEMO_AUTO_TRUST_SSH=1` (see `.env.example`). Prefer system `known_hosts` + reject unknown hosts for real use.
- Commands used: [docs/ssh-commands.md](docs/ssh-commands.md)
- Metrics keep **latest sample only** (no long history)

## Tests

```bash
pytest -q
```

## CI

GitHub Actions (`.github/workflows/ci.yml`) on push/PR to `main`: install deps → `pytest`. Uses a CI-only `SECRET_KEY` env var (no real secrets in logs).

## Security (demo baseline)

- Admin password hashed (Werkzeug)
- `SECRET_KEY` from environment when set
- CSRF on POST forms (Flask-WTF)
- SSH secrets never rendered back in edit forms
- Metric rows do not store SSH credentials
- `.env`, `*.db`, keys are gitignored
