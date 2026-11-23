from app.auth.passwords import verify_password


def register(client, headers, email="reader@example.com", full_name="Reader", password="correct-horse-battery"):
    return client.post(
        "/auth/register",
        headers=headers,
        json={"email": email, "full_name": full_name, "password": password},
    )


def test_register_hashes_password_and_creates_persistent_session(client, csrf_headers):
    from app.models import User

    response = register(client, csrf_headers)
    assert response.status_code == 201
    assert response.json()["email"] == "reader@example.com"
    assert "password_hash" not in response.json()
    assert "httponly" in response.headers["set-cookie"].lower()
    assert client.get("/users/me").json()["full_name"] == "Reader"
    db = app_test_db()
    try:
        stored_user = db.query(User).one()
        assert stored_user.password_hash != "correct-horse-battery"
        assert verify_password(stored_user.password_hash, "correct-horse-battery")
    finally:
        db.close()


def test_duplicate_email_and_invalid_login_are_rejected(client, csrf_headers):
    assert register(client, csrf_headers).status_code == 201
    client.post("/auth/logout", headers=csrf_headers)
    duplicate = register(client, csrf_headers)
    assert duplicate.status_code == 409
    case_variant = register(client, csrf_headers, email="READER@Example.com")
    assert case_variant.status_code == 409

    response = client.post(
        "/auth/login", headers=csrf_headers,
        json={"email": "reader@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_restores_session_and_logout_revokes_it(client, csrf_headers):
    assert register(client, csrf_headers).status_code == 201
    client.post("/auth/logout", headers=csrf_headers)
    assert client.get("/users/me").status_code == 401
    assert client.post(
        "/auth/login", headers=csrf_headers,
        json={"email": "reader@example.com", "password": "correct-horse-battery"},
    ).status_code == 200
    assert client.get("/users/me").status_code == 200
    assert client.post("/auth/logout", headers=csrf_headers).status_code == 200
    assert client.get("/users/me").status_code == 401


def test_login_rate_limit_is_per_ip_and_normalized_email(client, csrf_headers):
    assert register(client, csrf_headers).status_code == 201
    assert client.post("/auth/logout", headers=csrf_headers).status_code == 200
    for _ in range(10):
        response = client.post(
            "/auth/login", headers=csrf_headers,
            json={"email": " READER@example.com ", "password": "incorrect-password"},
        )
        assert response.status_code == 401
    blocked = client.post(
        "/auth/login", headers=csrf_headers,
        json={"email": "reader@example.com", "password": "incorrect-password"},
    )
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Too many requests. Try again later."


def test_profile_is_private_and_only_full_name_can_be_updated(client, csrf_headers):
    assert register(client, csrf_headers).status_code == 201
    updated = client.patch("/users/me", headers=csrf_headers, json={"full_name": "Updated Reader"})
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated Reader"
    assert client.patch("/users/me", headers=csrf_headers, json={"email": "attacker@example.com"}).status_code == 422
    assert client.post("/auth/logout", headers=csrf_headers).status_code == 200
    assert client.patch("/users/me", headers=csrf_headers, json={"full_name": "Intruder"}).status_code == 401
    assert client.get("/users/me").status_code == 401


def test_each_session_only_resolves_its_own_profile(client, csrf_headers):
    first = register(client, csrf_headers, email="first@example.com", full_name="First User")
    first_id = first.json()["id"]
    assert client.post("/auth/logout", headers=csrf_headers).status_code == 200
    second = register(client, csrf_headers, email="second@example.com", full_name="Second User")
    assert second.status_code == 201
    assert client.get("/users/me").json()["id"] == second.json()["id"]
    assert client.get("/users/me").json()["id"] != first_id
    assert client.post("/auth/logout", headers=csrf_headers).status_code == 200
    assert client.post(
        "/auth/login", headers=csrf_headers,
        json={"email": "first@example.com", "password": "correct-horse-battery"},
    ).status_code == 200
    assert client.get("/users/me").json()["id"] == first_id


def test_csrf_requires_valid_token_and_allowed_origin(client):
    response = client.post(
        "/auth/register", headers={"Origin": "https://evil.example"},
        json={"email": "a@example.com", "full_name": "A User", "password": "correct-horse-battery"},
    )
    assert response.status_code == 403
    response = client.post(
        "/auth/register", headers={"Origin": "http://localhost:3000"},
        json={"email": "a@example.com", "full_name": "A User", "password": "correct-horse-battery"},
    )
    assert response.status_code == 403


def test_registration_rate_limit_is_enforced(client, csrf_headers):
    for i in range(5):
        assert register(client, csrf_headers, email=f"reader{i}@example.com").status_code == 201
        assert client.post("/auth/logout", headers=csrf_headers).status_code == 200
    response = register(client, csrf_headers, email="reader5@example.com")
    assert response.status_code == 429
    assert response.headers.get("Retry-After")


def test_session_expiration_is_enforced(client, csrf_headers):
    from datetime import datetime, timedelta, timezone
    assert register(client, csrf_headers).status_code == 201
    db = app_test_db()
    try:
        from app.models import UserSession
        session = db.query(UserSession).one()
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()
    assert client.get("/users/me").status_code == 401


def app_test_db():
    from app.main import app
    from app.db.session import get_db
    generator = app.dependency_overrides[get_db]()
    return next(generator)
