"""Persist latest metrics per server. Never stores SSH credentials in snapshots."""

from __future__ import annotations

import logging

from flask import current_app

from app.collectors import collect_metrics_via_ssh
from app.extensions import db
from app.models import MetricHistory, MetricSnapshot, Server, utcnow
from app.ssh_client import SSHError

logger = logging.getLogger(__name__)


def _get_or_create_snapshot(server: Server) -> MetricSnapshot:
    snap = server.metrics
    if snap is None:
        snap = MetricSnapshot(server_id=server.id)
        db.session.add(snap)
        server.metrics = snap
    return snap


def _append_history(server: Server, data: dict) -> None:
    """Keep a short rolling history for graphs (no credentials)."""
    db.session.add(
        MetricHistory(
            server_id=server.id,
            collected_at=utcnow(),
            status=data.get("status", "ok"),
            cpu_percent=data.get("cpu_percent"),
            memory_percent=data.get("memory_percent"),
            network_rx_bytes=data.get("network_rx_bytes"),
            network_tx_bytes=data.get("network_tx_bytes"),
        )
    )
    limit = int(current_app.config.get("METRICS_HISTORY_LIMIT", 48))
    # Delete oldest beyond limit for this server
    old_ids = (
        MetricHistory.query.filter_by(server_id=server.id)
        .order_by(MetricHistory.collected_at.desc())
        .offset(limit)
        .with_entities(MetricHistory.id)
        .all()
    )
    if old_ids:
        MetricHistory.query.filter(
            MetricHistory.id.in_([row[0] for row in old_ids])
        ).delete(synchronize_session=False)


def save_success(server: Server, data: dict) -> MetricSnapshot:
    snap = _get_or_create_snapshot(server)
    snap.collected_at = utcnow()
    snap.status = data.get("status", "ok")
    snap.error_message = None
    snap.cpu_percent = data.get("cpu_percent")
    snap.memory_used_mb = data.get("memory_used_mb")
    snap.memory_total_mb = data.get("memory_total_mb")
    snap.memory_percent = data.get("memory_percent")
    snap.network_rx_bytes = data.get("network_rx_bytes")
    snap.network_tx_bytes = data.get("network_tx_bytes")
    snap.ports_json = data.get("ports_json")
    _append_history(server, data)
    db.session.commit()
    return snap


def save_failure(server: Server, message: str) -> MetricSnapshot:
    snap = _get_or_create_snapshot(server)
    snap.collected_at = utcnow()
    snap.status = "unreachable"
    snap.error_message = message[:500]
    # Leave last known metrics if any; only mark unreachable
    db.session.commit()
    return snap


def collect_and_store(server: Server) -> MetricSnapshot:
    """Collect metrics for one server; isolate failures."""
    cfg = current_app.config
    try:
        data = collect_metrics_via_ssh(
            host=server.host,
            port=server.port,
            username=server.ssh_username,
            password=server.ssh_password,
            private_key=server.ssh_private_key,
            timeout=cfg.get("SSH_CONNECT_TIMEOUT", 10),
            auto_trust=cfg.get("DEMO_AUTO_TRUST_SSH", True),
        )
        return save_success(server, data)
    except (SSHError, OSError, ValueError) as exc:
        logger.warning("Metrics collection failed for server_id=%s: %s", server.id, type(exc).__name__)
        return save_failure(server, str(exc))


def collect_all_servers() -> None:
    """Iterate all servers; failures on one do not stop others."""
    servers = Server.query.all()
    for server in servers:
        try:
            collect_and_store(server)
        except Exception:
            logger.exception("Unexpected error collecting server_id=%s", server.id)
            try:
                db.session.rollback()
                save_failure(server, "Unexpected collection error")
            except Exception:
                db.session.rollback()
                logger.exception("Failed to persist error for server_id=%s", server.id)
