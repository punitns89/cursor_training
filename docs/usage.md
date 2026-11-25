# Usage (local demo)

## Sign in

1. Open `http://127.0.0.1:5000`
2. Username: `admin` / Password: `admin123`
3. You land on the **Dashboard**

## Add / edit / delete servers

1. Open **Servers** → **Add server**
2. Fill required fields:
   - Name, Hostname/IP, SSH port (default `22`), SSH username
   - SSH password **or** PEM private key (at least one)
   - Optional tags (e.g. `dev`, `prod`)
3. **Edit** updates fields; leave password/key blank to keep existing secrets (they are never shown in the form)
4. **Delete** asks for confirmation

SSH credentials are stored in the local SQLite DB only and must not be committed.

## View metrics

1. **Dashboard** — status + CPU/memory glance, plus bar/line graphs across hosts
2. Click a server for **detail**: CPU, memory, network RX/TX, listening ports
3. Metrics refresh every **5 minutes**, or use **Refresh now** on the detail page
4. Line graphs use a short rolling history (last ~48 samples per server)

Collection uses read-only remote commands only (see [ssh-commands.md](./ssh-commands.md)).
