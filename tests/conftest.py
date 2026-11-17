import pytest
from pathlib import Path

from app import app
from lib.database_connection import DatabaseConnection


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def db_connection():
    connection = DatabaseConnection(test_mode=True)
    connection.connect()

    connection.seed(PROJECT_ROOT / "seeds" / "schema.sql")
    connection.seed(PROJECT_ROOT / "seeds" / "exercises_data.sql")

    yield connection

    connection.connection.close()


@pytest.fixture
def web_client(db_connection):
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client