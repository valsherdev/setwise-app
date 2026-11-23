from lib.user_repository import UserRepository


# --- SIGNUP TESTS ---
def test_signup_page_is_accessible(web_client):
    response = web_client.get("/")

    assert response.status_code == 200
    assert b"Sign up" in response.data


def test_successful_signup(web_client, db_connection):
    response = web_client.post("/", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 302
    assert response.location == "/dashboard"

    users = db_connection.execute(
        "SELECT * FROM users WHERE email = %s",
        ["test@example.com"]
    )
    assert len(users) == 1


def test_signup_duplicate_email(web_client, db_connection):
    repository = UserRepository(db_connection)
    repository.create({
        "username": "existing",
        "email": "test@example.com",
        "password": "password123"
    })

    response = web_client.post("/", data={
        "username": "another",
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.location == "/sign-up/failed"


def test_signup_empty_fields(web_client):
    response = web_client.post("/", data={
        "username": "",
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.location == "/sign-up/failed"


# --- LOGIN TESTS ---
def test_login_page_is_accessible(web_client):
    response = web_client.get("/sessions/new")

    assert response.status_code == 200
    assert b"Login" in response.data


def test_successful_login(web_client, db_connection):
    repository = UserRepository(db_connection)
    repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    response = web_client.post("/sessions", data={
        "email": "test@example.com",
        "password": "password123"
    })

    assert response.status_code == 302
    assert response.location == "/dashboard"


def test_login_wrong_password(web_client, db_connection):
    repository = UserRepository(db_connection)
    repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    response = web_client.post("/sessions", data={
        "email": "test@example.com",
        "password": "wrongpassword"
    })

    assert response.location == "/sessions/failed"


def test_login_unknown_email(web_client):
    response = web_client.post("/sessions", data={
        "email": "unknown@example.com",
        "password": "password123"
    })

    assert response.location == "/sessions/failed"


# --- FAIL PAGES TESTS ---
def test_signup_failure_page(web_client):
    response = web_client.get("/sign-up/failed")

    assert response.status_code == 200


def test_login_failure_page(web_client):
    response = web_client.get("/sessions/failed")

    assert response.status_code == 200


# --- AUTHENTICATION TESTS ---
def test_dashboard_requires_login(web_client):
    response = web_client.get("/dashboard")

    assert response.status_code == 302
    assert response.location == "/sessions/new"


# --- LOGOUT TESTS ---
def test_logout(web_client):
    with web_client.session_transaction() as session:
        session["user_id"] = 1

    response = web_client.get("/logout")

    assert response.status_code == 302
    assert response.location == "/"

    with web_client.session_transaction() as session:
        assert "user_id" not in session