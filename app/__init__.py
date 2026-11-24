"""Flask application factory."""

from pathlib import Path

from flask import Flask

from app.config import Config
from app.extensions import csrf, db


def create_app(config_object=None):
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parent.parent / "templates"),
        static_folder=str(Path(__file__).resolve().parent.parent / "static"),
    )
    app.config.from_object(config_object or Config)

    # Ensure instance path exists for SQLite
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    # If default sqlite path uses BASE_DIR/instance, ensure parent exists
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = Path(db_uri.replace("sqlite:///", "", 1))
        if db_path.parent and str(db_path.parent) not in ("", "."):
            db_path.parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.main import bp as main_bp
    from app.blueprints.servers import bp as servers_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(servers_bp)

    with app.app_context():
        db.create_all()
        _seed_admin(app)

    # Scheduler (skipped under TESTING)
    if not app.config.get("TESTING"):
        from app.scheduler import start_scheduler

        start_scheduler(app)

    @app.context_processor
    def inject_globals():
        from app.auth_utils import current_username, is_authenticated

        return {
            "current_username": current_username(),
            "is_authenticated": is_authenticated(),
        }

    return app


def _seed_admin(app):
    from app.models import User

    username = app.config["DEFAULT_ADMIN_USERNAME"]
    password = app.config["DEFAULT_ADMIN_PASSWORD"]
    if not User.query.filter_by(username=username).first():
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
