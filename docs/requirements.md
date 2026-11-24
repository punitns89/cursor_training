# PRD: Demo Linux Server Monitoring Infrastructure

## 1. Overview

A local demo web app that lets internal teams (L1 / L2 / L3, infra, and app development) view Linux server health without SSH-ing into each host.

**Problem:** Teams currently log into servers to check live memory, CPU, network, and port usage.

**Goal:** Provide a read-only monitoring UI, with an authenticated admin who can register Linux servers. Metrics are collected over SSH and refreshed every 5 minutes.

**Scope:** Demo only — run locally with a single Flask process. Keep setup and operations minimal.

---

## 2. Users

| Role | Who | Capabilities |
|------|-----|--------------|
| Admin | Single shared account (`admin`) | Sign in, view metrics, add / edit / delete servers |

No other roles or multi-user support in this demo.

---

## 3. Goals & Non-Goals

### Goals
- Friendly, attractive read-only monitoring UI
- Sign-in with default `admin` user and hashed default password
- Register Linux servers (SSH credentials stored) and collect metrics remotely
- Show CPU, memory, network, and port usage
- Auto-refresh metrics every 5 minutes
- Local run via a single Flask command

### Non-Goals (out of scope for demo)
- Alerts / notifications
- Historical graphs or long-term retention
- Multi-tenancy, RBAC beyond single admin
- HTTPS / production hardening
- Agents installed on target hosts
- Docker / multi-service deploy
- Windows or non-Linux targets

---

## 4. Features

### 4.1 Authentication
- Default username: `admin`
- Default password: `admin123` (documented; must be stored hashed, e.g. Werkzeug/bcrypt)
- Session: Flask signed cookie session
- Logout ends the session
- Unauthenticated users are redirected to login
- Metrics and server pages require login

### 4.2 Server management (admin)
Admin can **add**, **edit**, and **delete** Linux servers.

**Fields when adding/editing a server:**
| Field | Required | Notes |
|-------|----------|--------|
| Name / label | Yes | Display name |
| Hostname or IP | Yes | SSH target |
| SSH port | Yes | Default `22` |
| SSH username | Yes | Remote Linux user |
| SSH password **or** private key path/content | Yes | One auth method; stored by the app |
| Environment / tags | No | e.g. `dev`, `prod` (optional labels) |

- UI for metrics is read-only (no mutating remote systems from the dashboard)
- Server CRUD is the only write path in the UI

### 4.3 Metric collection (SSH)
- App connects to each registered server over SSH using stored credentials
- Collect and display:
  - **CPU** usage (%)
  - **Memory** usage (used / total / %)
  - **Network** usage (basic RX/TX rates or counters)
  - **Port** usage (listening ports / key service ports)
- Poll interval: **every 5 minutes** (background job or scheduled task inside the Flask app)
- Manual “Refresh now” on a server detail page is nice-to-have for demos
- On SSH/collection failure: show clear error state on that server (e.g. “unreachable”) without crashing the app

### 4.4 UI pages
1. **Login** — username / password
2. **Dashboard (overview)** — all servers with latest status and key metrics at a glance
3. **Server list** — searchable/simple table; actions to add / edit / delete
4. **Server detail** — CPU, memory, network, ports for one host; last collected timestamp

**UI direction:** Clean ops-style dashboard (light or dark), readable cards/tables, clear status indicators (OK / warning / unreachable). Prefer simple HTML + CSS (or lightweight templates); keep attractive but not over-engineered.

---

## 5. Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3 |
| Web | Flask + Jinja templates |
| Auth hashing | Werkzeug password hashing (or equivalent) |
| DB | SQLite (local file) |
| SSH | Paramiko (or equivalent) |
| Scheduling | In-process scheduler (e.g. APScheduler) or simple background thread every 5 minutes |
| Run | `flask run` or `python app.py` |

---

## 6. Data (minimal)

Persist in SQLite:
- Admin user record (username + password hash)
- Servers (connection + label fields)
- Latest metrics snapshot per server (timestamp + JSON or columns for CPU/mem/net/ports)

No long-term history required beyond “latest sample” (optional: keep last N samples only if easy).

---

## 7. Acceptance criteria

- [ ] App starts locally with one Flask command and uses SQLite
- [ ] Login works with `admin` / `admin123`; password stored hashed
- [ ] Session cookie protects all monitoring pages
- [ ] Admin can add, edit, and delete Linux servers (SSH fields saved)
- [ ] App SSHs to targets and shows CPU, memory, network, and port usage
- [ ] Metrics refresh automatically every 5 minutes
- [ ] Dashboard + server list + server detail are usable and read-only for metrics
- [ ] Failed SSH shows an error/unreachable state per server

---

## 8. Local run (minimal)

```bash
# from project root (after deps installed)
export FLASK_APP=app.py   # or as documented in README
flask run
```

Open `http://127.0.0.1:5000`, sign in as `admin` / `admin123`, add a Linux server with SSH details, view dashboard and detail pages.

---

## 9. Demo success definition

An L1/L2 engineer can log in locally, register a Linux host, and within one poll cycle (≤ 5 minutes, or immediate manual refresh if implemented) see CPU, memory, network, and port usage without logging into that server themselves.
