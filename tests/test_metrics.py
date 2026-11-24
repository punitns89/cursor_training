from unittest.mock import patch

from app.extensions import db
from app.metrics_service import collect_all_servers, collect_and_store, save_failure, save_success
from app.models import MetricSnapshot, Server
from app.scheduler import get_poll_interval_seconds


def _server(app, name="s1"):
    with app.app_context():
        s = Server(
            name=name,
            host="10.0.0.5",
            port=22,
            ssh_username="u",
            ssh_password="pw",
        )
        db.session.add(s)
        db.session.commit()
        return s.id


def test_save_success_and_failure(app):
    sid = _server(app)
    with app.app_context():
        server = db.session.get(Server, sid)
        snap = save_success(
            server,
            {
                "status": "ok",
                "cpu_percent": 12.5,
                "memory_used_mb": 100,
                "memory_total_mb": 200,
                "memory_percent": 50,
                "network_rx_bytes": 1,
                "network_tx_bytes": 2,
                "ports_json": "[]",
            },
        )
        assert snap.status == "ok"
        assert snap.cpu_percent == 12.5
        # No credential fields on snapshot
        assert not hasattr(snap, "ssh_password")

        snap2 = save_failure(server, "SSH connection failed")
        assert snap2.status == "unreachable"
        assert "SSH" in snap2.error_message


@patch("app.metrics_service.collect_metrics_via_ssh")
def test_collect_and_store_success(mock_collect, app):
    mock_collect.return_value = {
        "status": "ok",
        "cpu_percent": 5.0,
        "memory_used_mb": 10,
        "memory_total_mb": 100,
        "memory_percent": 10,
        "network_rx_bytes": 0,
        "network_tx_bytes": 0,
        "ports_json": "[]",
    }
    sid = _server(app, "ok-host")
    with app.app_context():
        server = db.session.get(Server, sid)
        snap = collect_and_store(server)
        assert snap.status == "ok"
        assert MetricSnapshot.query.filter_by(server_id=sid).count() == 1


@patch("app.metrics_service.collect_metrics_via_ssh", side_effect=OSError("down"))
def test_collect_and_store_failure(mock_collect, app):
    sid = _server(app, "bad-host")
    with app.app_context():
        server = db.session.get(Server, sid)
        snap = collect_and_store(server)
        assert snap.status == "unreachable"


@patch("app.metrics_service.collect_and_store")
def test_collect_all_invokes_per_server(mock_one, app):
    _server(app, "a")
    _server(app, "b")
    with app.app_context():
        collect_all_servers()
        assert mock_one.call_count == 2


def test_poll_interval_is_five_minutes(app):
    assert get_poll_interval_seconds(app) == 300
