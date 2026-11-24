"""Session-based auth helpers. Passwords are never logged."""

from functools import wraps

from flask import redirect, session, url_for


def login_user(user_id: int, username: str) -> None:
    session.clear()
    session["user_id"] = user_id
    session["username"] = username
    session.permanent = False


def logout_user() -> None:
    session.clear()


def current_username():
    return session.get("username")


def is_authenticated() -> bool:
    return "user_id" in session


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped
