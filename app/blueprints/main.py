"""Dashboard and home routes."""

import json

from flask import Blueprint, render_template

from app.auth_utils import login_required
from app.models import Server

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def dashboard():
    servers = Server.query.order_by(Server.name).all()
    cards = []
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
    return render_template("dashboard.html", cards=cards)


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
