import sqlite3

import pytest
from fastapi.testclient import TestClient

import db
from main import app


client = TestClient(app)


@pytest.fixture
def database_client(tmp_path, monkeypatch):
    database_path = tmp_path / "tasks.db"
    monkeypatch.setattr(db, "DATABASE_PATH", database_path)
    db.init_db()
    return client


def test_root_returns_online_status() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "online"}


def test_openapi_exposes_crud_routes() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "post" in paths["/tasks"]
    assert "get" in paths["/tasks"]
    assert "put" in paths["/tasks/{task_id}"]
    assert "delete" in paths["/tasks/{task_id}"]


def test_openapi_exposes_task_schemas() -> None:
    schemas = client.get("/openapi.json").json()["components"]["schemas"]

    assert set(schemas["TaskCreate"]["properties"]) == {"title", "hours"}
    assert set(schemas["TaskResponse"]["properties"]) == {
        "id",
        "title",
        "hours",
    }


def test_openapi_uses_integer_task_id() -> None:
    operation = client.get("/openapi.json").json()["paths"][
        "/tasks/{task_id}"
    ]["put"]
    task_id = next(
        parameter
        for parameter in operation["parameters"]
        if parameter["name"] == "task_id"
    )

    assert task_id["required"] is True
    assert task_id["schema"]["type"] == "integer"


def test_cors_allows_local_development_origin() -> None:
    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:3000"
    )
    assert "POST" in response.headers["access-control-allow-methods"]


def test_crud_lifecycle_persists_across_requests(database_client) -> None:
    create_response = database_client.post(
        "/tasks", json={"title": "Algorithms", "hours": 2.0}
    )
    assert create_response.status_code == 201
    assert create_response.json() == {
        "id": 1,
        "title": "Algorithms",
        "hours": 2.0,
    }

    list_response = database_client.get("/tasks")
    assert list_response.status_code == 200
    assert list_response.json() == [create_response.json()]

    update_response = database_client.put(
        "/tasks/1", json={"title": "Data Structures", "hours": 3.5}
    )
    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": 1,
        "title": "Data Structures",
        "hours": 3.5,
    }

    delete_response = database_client.delete("/tasks/1")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert database_client.get("/tasks").json() == []


def test_update_and_delete_unknown_task_return_not_found(
    database_client,
) -> None:
    update_response = database_client.put(
        "/tasks/999", json={"title": "Unknown", "hours": 1.0}
    )
    delete_response = database_client.delete("/tasks/999")

    assert update_response.status_code == 404
    assert update_response.json() == {"detail": "Task not found"}
    assert delete_response.status_code == 404
    assert delete_response.json() == {"detail": "Task not found"}


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
def test_create_rejects_invalid_task_data(database_client, payload) -> None:
    response = database_client.post("/tasks", json=payload)

    assert response.status_code == 400
    assert database_client.get("/tasks").json() == []


def test_parameter_binding_stores_sql_injection_as_text(
    database_client,
) -> None:
    malicious_title = "Task'); DROP TABLE tasks; --"

    response = database_client.post(
        "/tasks", json={"title": malicious_title, "hours": 1.0}
    )

    assert response.status_code == 201
    assert response.json()["title"] == malicious_title
    with sqlite3.connect(db.DATABASE_PATH) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE name = ?", ("tasks",)
        ).fetchone()
    assert table is not None
