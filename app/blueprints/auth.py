"""Login / logout routes."""

from flask import Blueprint, flash, redirect, render_template, url_for

from app.auth_utils import is_authenticated, login_user, logout_user
from app.forms import LoginForm
from app.models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        # Always call check on a dummy path length — use real verify only when user exists
        if user and user.check_password(form.password.data):
            login_user(user.id, user.username)
            return redirect(url_for("main.dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html", form=form)


@bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("auth.login"))
