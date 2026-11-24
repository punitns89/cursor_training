import json

from app.extensions import db
from app.models import MetricSnapshot, Server


def test_dashboard_and_detail_with_metrics(auth_client, app):
    with app.app_context():
        s = Server(
            name="web",
            host="10.0.0.9",
            port=22,
            ssh_username="u",
            ssh_password="pw",
            tags="dev",
        )
        db.session.add(s)
        db.session.flush()
        snap = MetricSnapshot(
            server_id=s.id,
            status="ok",
            cpu_percent=11.0,
            memory_percent=42.0,
            memory_used_mb=420,
            memory_total_mb=1000,
            network_rx_bytes=100,
            network_tx_bytes=200,
            ports_json=json.dumps([{"address": "0.0.0.0", "port": "22"}]),
        )
        db.session.add(snap)
        db.session.commit()
        sid = s.id

    dash = auth_client.get("/")
    assert dash.status_code == 200
    assert b"web" in dash.data
    assert b"11.0" in dash.data or b"11%" in dash.data or b"11.0%" in dash.data

    detail = auth_client.get(f"/servers/{sid}")
    assert detail.status_code == 200
    assert b"Listening ports" in detail.data
    assert b"22" in detail.data
    # Read-only: no SSH password in page
    assert b">pw<" not in detail.data


def test_dashboard_requires_auth(client):
    assert client.get("/", follow_redirects=False).status_code == 302
