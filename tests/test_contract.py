from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


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
