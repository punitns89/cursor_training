"""Dashboard and home routes."""

import json
from collections import defaultdict

from flask import Blueprint, render_template

from app.auth_utils import login_required
from app.models import MetricHistory, Server

bp = Blueprint("main", __name__)

# Distinct series colors for multi-server line charts (dark UI)
_SERIES_COLORS = [
    "#3d9cf0",
    "#3ecf8e",
    "#e6a817",
    "#c084fc",
    "#22d3ee",
    "#fb7185",
    "#a3e635",
    "#f97316",
]


def _dataset(label, data, color):
    return {
        "label": label,
        "data": data,
        "borderColor": color,
        "backgroundColor": color + "33",
        "tension": 0.3,
        "spanGaps": True,
    }


@bp.route("/")
@login_required
def dashboard():
    servers = Server.query.order_by(Server.name).all()
    cards = []
    bar_labels = []
    bar_cpu = []
    bar_mem = []

    for s in servers:
        m = s.metrics
        cards.append(
            {
                "server": s,
                "status": m.status if m else "unknown",
                "cpu_percent": m.cpu_percent if m else None,
                "memory_percent": m.memory_percent if m else None,
                "collected_at": m.collected_at if m else None,
                "error_message": m.error_message if m else None,
            }
        )
        bar_labels.append(s.name)
        bar_cpu.append(m.cpu_percent if m and m.cpu_percent is not None else 0)
        bar_mem.append(m.memory_percent if m and m.memory_percent is not None else 0)

    history_rows = []
    if servers:
        history_rows = (
            MetricHistory.query.filter(MetricHistory.server_id.in_([s.id for s in servers]))
            .order_by(MetricHistory.collected_at.asc())
            .all()
        )

    timestamps = sorted({h.collected_at for h in history_rows})
    by_server = defaultdict(dict)
    for h in history_rows:
        by_server[h.server_id][h.collected_at] = h

    cpu_datasets = []
    mem_datasets = []

    if timestamps:
        label_strings = [
            ts.strftime("%H:%M:%S") if hasattr(ts, "strftime") else str(ts)
            for ts in timestamps
        ]
        for idx, s in enumerate(servers):
            color = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
            cpu_points = []
            mem_points = []
            for ts in timestamps:
                point = by_server[s.id].get(ts)
                cpu_points.append(
                    point.cpu_percent if point and point.cpu_percent is not None else None
                )
                mem_points.append(
                    point.memory_percent if point and point.memory_percent is not None else None
                )
            cpu_datasets.append(_dataset(s.name, cpu_points, color))
            mem_datasets.append(_dataset(s.name, mem_points, color))
    else:
        # Fallback: single "now" point from latest snapshot so graphs aren't empty
        label_strings = ["now"]
        for idx, s in enumerate(servers):
            color = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
            m = s.metrics
            cpu_datasets.append(
                _dataset(s.name, [m.cpu_percent if m else None], color)
            )
            mem_datasets.append(
                _dataset(s.name, [m.memory_percent if m else None], color)
            )

    charts = {
        "bar_labels": bar_labels,
        "bar_cpu": bar_cpu,
        "bar_mem": bar_mem,
        "line_labels": label_strings,
        "cpu_datasets": cpu_datasets,
        "mem_datasets": mem_datasets,
        "has_line_data": any(
            any(v is not None for v in ds["data"]) for ds in cpu_datasets
        ),
    }

    return render_template(
        "dashboard.html",
        cards=cards,
        charts_json=json.dumps(charts),
    )


@bp.route("/servers/<int:server_id>")
@login_required
def server_detail(server_id):
    server = Server.query.get_or_404(server_id)
    m = server.metrics
    ports = []
    if m and m.ports_json:
        try:
            ports = json.loads(m.ports_json)
        except json.JSONDecodeError:
            ports = []
    return render_template(
        "servers/detail.html",
        server=server,
        metrics=m,
        ports=ports,
    )
