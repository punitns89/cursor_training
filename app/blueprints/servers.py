"""Server CRUD — metrics remain read-only; this is the only write path."""

from flask import Blueprint, flash, redirect, render_template, url_for
from wtforms.validators import ValidationError

from app.auth_utils import login_required
from app.extensions import db
from app.forms import ServerForm
from app.metrics_service import collect_and_store
from app.models import Server

bp = Blueprint("servers", __name__, url_prefix="/servers")


@bp.route("/")
@login_required
def list_servers():
    servers = Server.query.order_by(Server.name).all()
    return render_template("servers/list.html", servers=servers)


@bp.route("/add", methods=["GET", "POST"])
@login_required
def add_server():
    form = ServerForm()
    if form.validate_on_submit():
        try:
            form.require_auth_present()
        except ValidationError as exc:
            form.ssh_password.errors.append(str(exc))
            return render_template("servers/form.html", form=form, title="Add server")

        server = Server(
            name=form.name.data.strip(),
            host=form.host.data.strip(),
            port=form.port.data,
            ssh_username=form.ssh_username.data.strip(),
            ssh_password=form.ssh_password.data or None,
            ssh_private_key=(form.ssh_private_key.data or "").strip() or None,
            tags=(form.tags.data or "").strip() or None,
        )
        db.session.add(server)
        db.session.commit()
        flash(f"Server “{server.name}” added.", "success")
        return redirect(url_for("servers.list_servers"))
    return render_template("servers/form.html", form=form, title="Add server")


@bp.route("/<int:server_id>/edit", methods=["GET", "POST"])
@login_required
def edit_server(server_id):
    server = Server.query.get_or_404(server_id)
    form = ServerForm()

    if form.validate_on_submit():
        try:
            form.require_auth_present(existing=server)
        except ValidationError as exc:
            form.ssh_password.errors.append(str(exc))
            return render_template(
                "servers/form.html", form=form, title="Edit server", server=server
            )

        server.name = form.name.data.strip()
        server.host = form.host.data.strip()
        server.port = form.port.data
        server.ssh_username = form.ssh_username.data.strip()
        server.tags = (form.tags.data or "").strip() or None
        if form.ssh_password.data:
            server.ssh_password = form.ssh_password.data
        if form.ssh_private_key.data and form.ssh_private_key.data.strip():
            server.ssh_private_key = form.ssh_private_key.data.strip()
        db.session.commit()
        flash(f"Server “{server.name}” updated.", "success")
        return redirect(url_for("servers.list_servers"))

    if not form.is_submitted():
        form.name.data = server.name
        form.host.data = server.host
        form.port.data = server.port
        form.ssh_username.data = server.ssh_username
        form.tags.data = server.tags or ""
        # Never prefill secrets into HTML
        form.ssh_password.data = ""
        form.ssh_private_key.data = ""

    return render_template(
        "servers/form.html", form=form, title="Edit server", server=server
    )


@bp.route("/<int:server_id>/delete", methods=["POST"])
@login_required
def delete_server(server_id):
    server = Server.query.get_or_404(server_id)
    name = server.name
    db.session.delete(server)
    db.session.commit()
    flash(f"Server “{name}” deleted.", "info")
    return redirect(url_for("servers.list_servers"))


@bp.route("/<int:server_id>/refresh", methods=["POST"])
@login_required
def refresh_server(server_id):
    """Manual refresh — still read-only remote commands only."""
    server = Server.query.get_or_404(server_id)
    snap = collect_and_store(server)
    if snap.status == "unreachable":
        flash(f"Refresh failed: {snap.error_message}", "error")
    else:
        flash("Metrics refreshed.", "success")
    return redirect(url_for("main.server_detail", server_id=server.id))
