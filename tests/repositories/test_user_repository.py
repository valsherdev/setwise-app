from lib.user_repository import UserRepository
from flask_bcrypt import check_password_hash


def test_create_user(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    user = repository.find_by_email("test@example.com")

    assert user.id == 1
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert check_password_hash(user.password, "password123")


def test_find_by_email_returns_none_when_user_does_not_exist(db_connection):
    repository = UserRepository(db_connection)

    user = repository.find_by_email("unknown@example.com")

    assert user is None


def test_find_by_id(db_connection):
    repository = UserRepository(db_connection)

    created_user = repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    user = repository.find_by_id(created_user.id)

    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_find_by_id_returns_none_when_user_does_not_exist(db_connection):
    repository = UserRepository(db_connection)

    user = repository.find_by_id(999)

    assert user is None


def test_check_password_returns_true_for_correct_password(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    user = repository.find_by_email("test@example.com")

    assert repository.check_password(user, "password123") is True


def test_check_password_returns_false_for_incorrect_password(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    user = repository.find_by_email("test@example.com")

    assert repository.check_password(user, "wrongpassword") is False


def test_create_user_returns_false_when_username_is_empty(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "",
        "email": "test@example.com",
        "password": "password123"
    })

    assert user is False


def test_create_user_returns_false_when_email_is_empty(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "email": "",
        "password": "password123"
    })

    assert user is False


def test_create_user_returns_false_when_password_is_empty(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": ""
    })

    assert user is False


def test_returns_false_when_username_is_missing(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "email": "test@example.com",
        "password": "password123"
    })

    assert user is False


def test_returns_false_when_email_is_missing(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "password": "password123"
    })

    assert user is False


def test_returns_false_when_password_is_missing(db_connection):
    repository = UserRepository(db_connection)

    user = repository.create({
        "username": "testuser",
        "email": "test@example.com"
    })

    assert user is False


def test_create_user_returns_false_when_username_already_exists(db_connection):
    repository = UserRepository(db_connection)

    repository.create({
        "username": "testuser",
        "email": "first@example.com",
        "password": "password123"
    })

    user = repository.create({
        "username": "testuser",
        "email": "second@example.com",
        "password": "password123"
    })

    assert user is False


def test_create_user_returns_false_when_email_already_exists(db_connection):
    repository = UserRepository(db_connection)

    repository.create({
        "username": "firstuser",
        "email": "test@example.com",
        "password": "password123"
    })

    user = repository.create({
        "username": "seconduser",
        "email": "test@example.com",
        "password": "password123"
    })

    assert user is False


def test_database_connection_works_after_duplicate_user(db_connection):
    repository = UserRepository(db_connection)

    repository.create({
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    })

    repository.create({
        "username": "testuser",
        "email": "another@example.com",
        "password": "password123"
    })

    users = db_connection.execute("SELECT * FROM users")

    assert len(users) == 1