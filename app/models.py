"""SQLAlchemy models. SSH secrets are never rendered in templates."""

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Constant-time verification via Werkzeug."""
        return check_password_hash(self.password_hash, password)


class Server(db.Model):
    __tablename__ = "servers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False, default=22)
    ssh_username = db.Column(db.String(128), nullable=False)
    # Sensitive — never echo in templates or logs
    ssh_password = db.Column(db.Text, nullable=True)
    ssh_private_key = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    metrics = db.relationship(
        "MetricSnapshot",
        back_populates="server",
        uselist=False,
        cascade="all, delete-orphan",
    )
    history = db.relationship(
        "MetricHistory",
        back_populates="server",
        cascade="all, delete-orphan",
        order_by="MetricHistory.collected_at",
    )

    def has_ssh_auth(self) -> bool:
        return bool(self.ssh_password) or bool(self.ssh_private_key)


class MetricHistory(db.Model):
    """Short rolling history for dashboard graphs. No SSH credentials."""

    __tablename__ = "metric_history"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey("servers.id"), nullable=False, index=True)
    collected_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    status = db.Column(db.String(32), nullable=False, default="ok")
    cpu_percent = db.Column(db.Float, nullable=True)
    memory_percent = db.Column(db.Float, nullable=True)
    network_rx_bytes = db.Column(db.BigInteger, nullable=True)
    network_tx_bytes = db.Column(db.BigInteger, nullable=True)

    server = db.relationship("Server", back_populates="history")


class MetricSnapshot(db.Model):
    """Latest metrics (demo). Does not store SSH credentials."""

    __tablename__ = "metric_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(
        db.Integer, db.ForeignKey("servers.id"), unique=True, nullable=False
    )
    collected_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    status = db.Column(db.String(32), nullable=False, default="ok")  # ok | warning | unreachable
    error_message = db.Column(db.Text, nullable=True)
    # JSON payload: cpu, memory, network, ports — no credentials
    cpu_percent = db.Column(db.Float, nullable=True)
    memory_used_mb = db.Column(db.Float, nullable=True)
    memory_total_mb = db.Column(db.Float, nullable=True)
    memory_percent = db.Column(db.Float, nullable=True)
    network_rx_bytes = db.Column(db.BigInteger, nullable=True)
    network_tx_bytes = db.Column(db.BigInteger, nullable=True)
    ports_json = db.Column(db.Text, nullable=True)  # JSON list of listening ports

    server = db.relationship("Server", back_populates="metrics")
