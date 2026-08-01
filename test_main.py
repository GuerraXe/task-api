from collections.abc import Generator
from pathlib import Path
import sqlite3

import pytest
from fastapi.testclient import TestClient

from db import get_db
from main import app


TEST_DATABASE_PATH = Path(__file__).with_name("test_tasks.db")


def override_get_db() -> Generator[sqlite3.Connection, None, None]:
    connection = sqlite3.connect(
        TEST_DATABASE_PATH,
        timeout=5.0,
        check_same_thread=False,
    )
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


@pytest.fixture
def reset_test_database():
    if TEST_DATABASE_PATH.exists():
        TEST_DATABASE_PATH.unlink()

    setup_connection = sqlite3.connect(TEST_DATABASE_PATH)
    try:
        setup_connection.execute(
            """
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                hours REAL
            )
            """
        )
        setup_connection.commit()
    finally:
        setup_connection.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)
        if TEST_DATABASE_PATH.exists():
            TEST_DATABASE_PATH.unlink()


@pytest.fixture
def client(reset_test_database):
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()


def test_root_returns_online_status(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "online"}


def test_empty_database_returns_empty_task_list(client) -> None:
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_create_and_list_task_across_requests(client) -> None:
    create_response = client.post(
        "/tasks", json={"title": "Algorithms", "hours": 2.0}
    )
    list_response = client.get("/tasks")

    assert create_response.status_code == 201
    assert create_response.json() == {
        "id": 1,
        "title": "Algorithms",
        "hours": 2.0,
    }
    assert list_response.status_code == 200
    assert list_response.json() == [create_response.json()]


def test_update_existing_task(client) -> None:
    created = client.post(
        "/tasks", json={"title": "Algorithms", "hours": 2.0}
    ).json()

    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "Data Structures", "hours": 3.5},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": created["id"],
        "title": "Data Structures",
        "hours": 3.5,
    }


def test_delete_existing_task(client) -> None:
    task_id = client.post(
        "/tasks", json={"title": "Algorithms", "hours": 2.0}
    ).json()["id"]

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/tasks").json() == []


def test_update_unknown_task_returns_not_found(client) -> None:
    response = client.put(
        "/tasks/999", json={"title": "Unknown", "hours": 1.0}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


def test_delete_unknown_task_returns_not_found(client) -> None:
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "hours": 1.0},
        {"title": "   ", "hours": 1.0},
        {"title": "Algorithms", "hours": -1.0},
        {"title": "Algorithms", "hours": "letters"},
        {"title": "Algorithms"},
    ],
)
def test_create_rejects_invalid_task_data(client, payload) -> None:
    response = client.post("/tasks", json=payload)

    assert response.status_code == 400
    assert client.get("/tasks").json() == []


def test_sql_injection_text_does_not_change_schema(client) -> None:
    malicious_title = "Task'); DROP TABLE tasks; --"

    response = client.post(
        "/tasks", json={"title": malicious_title, "hours": 1.0}
    )

    assert response.status_code == 201
    assert response.json()["title"] == malicious_title
    connection = sqlite3.connect(TEST_DATABASE_PATH)
    try:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE name = ?", ("tasks",)
        ).fetchone()
    finally:
        connection.close()
    assert table is not None
