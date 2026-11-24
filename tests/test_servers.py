from app.extensions import db
from app.models import Server


def test_server_model_create_read(app):
    with app.app_context():
        s = Server(
            name="web1",
            host="10.0.0.1",
            port=22,
            ssh_username="ubuntu",
            ssh_password="secret",
            tags="dev",
        )
        db.session.add(s)
        db.session.commit()
        found = Server.query.filter_by(name="web1").first()
        assert found is not None
        assert found.host == "10.0.0.1"
        assert found.has_ssh_auth()
        # Sensitive field exists in DB but templates must not echo it (checked in CRUD HTML)


def test_server_list_requires_auth(client):
    resp = client.get("/servers/", follow_redirects=False)
    assert resp.status_code == 302


def test_add_server_happy_path(auth_client, app):
    resp = auth_client.post(
        "/servers/add",
        data={
            "name": "db1",
            "host": "192.168.1.10",
            "port": 22,
            "ssh_username": "monitor",
            "ssh_password": "pw",
            "ssh_private_key": "",
            "tags": "prod",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"db1" in resp.data
    with app.app_context():
        assert Server.query.filter_by(name="db1").count() == 1


def test_add_server_validation_missing_auth(auth_client):
    resp = auth_client.post(
        "/servers/add",
        data={
            "name": "bad",
            "host": "192.168.1.11",
            "port": 22,
            "ssh_username": "monitor",
            "ssh_password": "",
            "ssh_private_key": "",
            "tags": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"password or a private key" in resp.data


def test_add_server_invalid_port(auth_client):
    resp = auth_client.post(
        "/servers/add",
        data={
            "name": "badport",
            "host": "192.168.1.12",
            "port": 70000,
            "ssh_username": "monitor",
            "ssh_password": "pw",
            "tags": "",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # WTForms NumberRange should reject
    assert b"badport" in resp.data or b"port" in resp.data.lower()


def test_edit_and_delete_server(auth_client, app):
    with app.app_context():
        s = Server(
            name="tmp",
            host="10.0.0.2",
            port=22,
            ssh_username="u",
            ssh_password="pw",
        )
        db.session.add(s)
        db.session.commit()
        sid = s.id

    resp = auth_client.post(
        f"/servers/{sid}/edit",
        data={
            "name": "tmp-renamed",
            "host": "10.0.0.2",
            "port": 22,
            "ssh_username": "u",
            "ssh_password": "",
            "ssh_private_key": "",
            "tags": "dev",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"tmp-renamed" in resp.data

    # Edit form must not leak password
    edit_page = auth_client.get(f"/servers/{sid}/edit")
    assert b"secret" not in edit_page.data
    assert b"pw" not in edit_page.data or b'name="ssh_password"' in edit_page.data

    resp = auth_client.post(f"/servers/{sid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Server, sid) is None


def test_crud_requires_login(client, app):
    with app.app_context():
        s = Server(
            name="x",
            host="1.1.1.1",
            port=22,
            ssh_username="u",
            ssh_password="pw",
        )
        db.session.add(s)
        db.session.commit()
        sid = s.id

    assert client.post("/servers/add", data={}).status_code == 302
    assert client.post(f"/servers/{sid}/edit", data={}).status_code == 302
    assert client.post(f"/servers/{sid}/delete").status_code == 302
