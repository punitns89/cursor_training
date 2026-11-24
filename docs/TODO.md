# TODO: Demo Linux Server Monitoring

Small, AI-friendly increments. Check items off as you complete them.  
Demo only — local Flask run. Keep each step minimal.

Reference: [requirements.md](./requirements.md)

---

## 1. Project initialization and basic UI

- [x] **1.1** Create project layout (`app/`, `templates/`, `static/`, `tests/`, `docs/`)
- [x] **1.2** Add `requirements.txt` (Flask, pytest minimal set for now)
- [x] **1.3** Add `.gitignore` (venv, `__pycache__`, `.env`, `*.db`, secrets)
- [x] **1.4** Create minimal Flask app entry (`app.py` or `app/__init__.py`) that serves a home page
- [x] **1.5** Add base Jinja layout + simple attractive CSS (ops-style dashboard shell)
- [x] **1.6** Add placeholder pages: Dashboard, Servers (empty content OK)
- [x] **1.7** **Security:** Do not commit secrets; use a non-committed config pattern from day one
- [x] **1.8** **Docs:** Add root `README.md` with how to create venv, install deps, and `flask run`

---

## 2. Sign-in and unit tests

- [x] **2.1** Add SQLite + User model (single `admin` row)
- [x] **2.2** Seed default user `admin` with **hashed** password `admin123` (Werkzeug)
- [x] **2.3** Add login form page (username / password)
- [x] **2.4** Implement login POST + Flask signed session cookie
- [x] **2.5** Implement logout (clear session)
- [x] **2.6** Protect dashboard/server routes — redirect unauthenticated users to login
- [x] **2.7** **Security:** Constant-time password check via library hash verify; never log passwords; set `SECRET_KEY` from env (with safe local default documented)
- [x] **2.8** **Tests:** Unit tests for hash/verify, login success, login failure, logout, protected-route redirect
- [x] **2.9** **Docs:** Document default credentials and how to change `SECRET_KEY` in `README.md`

---

## 3. CI/CD (GitHub Actions)

- [x] **3.1** Add `.github/workflows/ci.yml`
- [x] **3.2** CI jobs: install deps → run pytest → (optional) basic lint if already configured
- [x] **3.3** Trigger on push/PR to `main`
- [x] **3.4** **Security:** No secrets in workflow logs; use env for `SECRET_KEY` in tests only
- [x] **3.5** **Docs:** Short “CI” section in `README.md` describing what the workflow runs

---

## 4. Database foundation for servers

- [x] **4.1** Add Server model (name, host, port, ssh_user, auth fields, tags)
- [x] **4.2** DB init/migrate path that creates tables on first run (keep demo-simple)
- [x] **4.3** **Security:** Plan credential storage — never echo SSH secrets in templates/logs; mark sensitive columns
- [x] **4.4** **Tests:** Model create/read smoke tests with temp SQLite
- [x] **4.5** **Docs:** Note DB file location and that it is local-only / gitignored

---

## 5. Server CRUD (UI + API routes)

- [x] **5.1** Server list page (table; empty state)
- [x] **5.2** Add-server form (required fields per PRD; SSH port default `22`)
- [x] **5.3** Create server (POST) — validate required fields
- [x] **5.4** Edit server form + update (POST)
- [x] **5.5** Delete server (POST with confirm in UI)
- [x] **5.6** Require login for all CRUD routes
- [x] **5.7** **Security:** CSRF protection on mutating forms (Flask-WTF or equivalent); mask password/key in edit forms; never return secrets in HTML source
- [x] **5.8** **Tests:** CRUD happy paths + auth-required + validation failures
- [x] **5.9** **Docs:** Document server fields and add/edit/delete flow in `README.md` or `docs/usage.md`

---

## 6. SSH client (collection building block)

- [x] **6.1** Add Paramiko (or equivalent) dependency
- [x] **6.2** Implement thin SSH helper: connect with password **or** private key
- [x] **6.3** Run a harmless remote command (`uname -a` or similar) for connectivity check
- [x] **6.4** **Security:** Disable unknown-host auto-trust in a documented way for demo (or pin host keys if easy); timeouts; never log private keys/passwords
- [x] **6.5** **Tests:** Unit tests with mocked SSH (no real network required in CI)
- [x] **6.6** **Docs:** Document SSH auth options and demo limitations

---

## 7. Metric collectors (read-only remote commands)

- [x] **7.1** Collect **CPU** usage (%) over SSH
- [x] **7.2** Collect **memory** (used / total / %)
- [x] **7.3** Collect **network** (basic RX/TX)
- [x] **7.4** Collect **listening ports**
- [x] **7.5** Parse into a single metrics DTO/dict
- [x] **7.6** **Security:** Commands must be read-only; no remote writes; sanitize/allowlist remote command strings
- [x] **7.7** **Tests:** Parser unit tests with fixture command outputs
- [x] **7.8** **Docs:** List which remote commands are used (for L1/L2 transparency)

---

## 8. Persist latest metrics + error state

- [x] **8.1** Metrics snapshot model/table (per server, timestamp, payload, status)
- [x] **8.2** Save success snapshot after collection
- [x] **8.3** On SSH/parse failure, store `unreachable` / error message without crashing app
- [x] **8.4** **Security:** Do not store raw SSH credentials inside metrics rows
- [x] **8.5** **Tests:** Success + failure persistence paths
- [x] **8.6** **Docs:** Explain “latest only” retention for the demo

---

## 9. 5-minute scheduler

- [x] **9.1** Add in-process scheduler (APScheduler or background thread)
- [x] **9.2** Job: iterate servers → collect → save snapshots every **5 minutes**
- [x] **9.3** Ensure scheduler starts once with the Flask app (avoid double-start in reloader if practical)
- [x] **9.4** **Security:** Job runs with least privilege in-app; isolate failures per server
- [x] **9.5** **Tests:** Job invokes collector for N servers (mocked); interval constant documented/tested
- [x] **9.6** **Docs:** Note poll interval and that first data may take up to 5 minutes

---

## 10. Dashboard and server detail (read-only metrics UI)

- [x] **10.1** Dashboard overview: all servers + status + key metrics
- [x] **10.2** Server detail page: CPU, memory, network, ports + last collected time
- [x] **10.3** Status indicators: OK / warning / unreachable
- [x] **10.4** (Nice-to-have) Manual “Refresh now” on detail page
- [x] **10.5** **Security:** Metrics views remain read-only; no remote mutation controls in UI
- [x] **10.6** **Tests:** Detail/dashboard render with fixture metrics; unauthenticated redirect
- [x] **10.7** **Docs:** Screenshot-free walkthrough: login → add server → wait/refresh → view metrics

---

## 11. Polish, hardening, demo readiness

- [x] **11.1** Consistent empty/error states across pages
- [x] **11.2** Basic input validation (host, port range, required SSH auth method)
- [x] **11.3** **Security:** Review — secrets gitignored, hashed admin password, CSRF on writes, no secret leakage in templates/logs
- [x] **11.4** Confirm CI still green (pytest + workflow)
- [x] **11.5** **Docs:** Final `README.md` minimal run steps matching PRD §8; link to `requirements.md` and this TODO
- [x] **11.6** Smoke-check acceptance criteria from PRD §7 locally

---

## Suggested order for AI-assisted sessions

Work **one checkbox group (or even one checkbox) per session**. Prefer:

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11

Do not skip security or docs checkboxes in a step — they are part of “done.”
