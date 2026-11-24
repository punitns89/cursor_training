"""Application configuration. Secrets come from environment, not source control."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Default local-demo config. Override SECRET_KEY via environment in real use."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'monitoring.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Default admin (password stored hashed at seed time — never store plaintext in DB)
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"

    # Metric poll interval (seconds)
    METRICS_POLL_INTERVAL_SECONDS = 300  # 5 minutes

    # SSH
    SSH_CONNECT_TIMEOUT = 10
    # Demo convenience: when "1", AutoAddPolicy is used. Prefer known_hosts in real use.
    DEMO_AUTO_TRUST_SSH = os.environ.get("DEMO_AUTO_TRUST_SSH", "1") == "1"


class TestConfig(Config):
    """In-memory DB and fixed secret for automated tests."""

    TESTING = True
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    DEMO_AUTO_TRUST_SSH = True
    METRICS_POLL_INTERVAL_SECONDS = 300
