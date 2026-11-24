from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User


def test_password_hash_and_verify():
    hashed = generate_password_hash("admin123")
    assert hashed != "admin123"
    assert check_password_hash(hashed, "admin123")
    assert not check_password_hash(hashed, "wrong")


def test_seeded_admin_has_hashed_password(app):
    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        assert user is not None
        assert user.password_hash != "admin123"
        assert user.check_password("admin123")
        assert not user.check_password("nope")


def test_login_success(client):
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login" not in resp.headers["Location"]


def test_login_failure(client):
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data


def test_logout(auth_client):
    resp = auth_client.post("/logout", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    # Protected route redirects after logout
    resp2 = auth_client.get("/", follow_redirects=False)
    assert resp2.status_code == 302
    assert "/login" in resp2.headers["Location"]


def test_protected_route_redirect(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    resp = client.get("/servers/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
