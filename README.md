# Task Organizer API

A small REST API for creating and managing tasks with estimated work hours. It is built with FastAPI, Pydantic, and SQLite and includes isolated pytest integration tests.

## Features

- Validated task creation and updates
- SQLite persistence with generated task IDs
- Parameterized SQL queries to prevent SQL injection
- Correct `201`, `204`, `400`, and `404` responses
- Interactive OpenAPI documentation
- CORS support for local frontend development
- Integration tests using a disposable SQLite database

## Technology

- Python
- FastAPI and Uvicorn
- Pydantic
- SQLite
- pytest and FastAPI `TestClient`

## Setup

Clone the repository and enter it:

```powershell
git clone https://github.com/GuerraXe/task-api.git
cd task-api
```

Create and activate a virtual environment on Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```powershell
python -m pip install fastapi uvicorn pydantic pytest httpx
```

## Run the API

Start the application from the project directory:

```powershell
python main.py
```

This initializes `tasks.db` when necessary and starts Uvicorn at:

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI document: <http://127.0.0.1:8000/openapi.json>

Stop the server with `Ctrl+C`.

## API

| Method | Route | Purpose | Success |
|---|---|---|---:|
| `GET` | `/` | Check API status | `200` |
| `POST` | `/tasks` | Create a task | `201` |
| `GET` | `/tasks` | List all tasks | `200` |
| `PUT` | `/tasks/{task_id}` | Replace a task | `200` |
| `DELETE` | `/tasks/{task_id}` | Delete a task | `204` |

A task request uses this shape:

```json
{
  "title": "Study algorithms",
  "hours": 2.5
}
```

A successful response includes its generated ID:

```json
{
  "id": 1,
  "title": "Study algorithms",
  "hours": 2.5
}
```

### PowerShell example

With the server running:

```powershell
curl.exe -i -X POST `
  -H "Content-Type: application/json" `
  -d '{\"title\":\"Study algorithms\",\"hours\":2.5}' `
  http://127.0.0.1:8000/tasks
```

## Tests

Run the complete suite:

```powershell
python -m pytest -v
```

The API integration tests override FastAPI's `get_db` dependency and use `test_tasks.db`. The schema is recreated before every test, connections are closed during teardown, and the test file is removed afterward. Tests do not read or write the development `tasks.db`.

## Project Structure

```text
task-api/
├── main.py                 # FastAPI application and CRUD routes
├── db.py                   # SQLite initialization and connection dependency
├── test_main.py            # Isolated API integration tests
├── tests/
│   ├── test_contract.py    # OpenAPI and CORS contract tests
│   └── test_db.py          # Database lifecycle tests
└── .gitignore              # Virtual environments and local databases
```

## Development Notes

- SQL request values are always passed through SQLite `?` placeholders.
- `tasks.db` and `test_tasks.db` are intentionally excluded from Git.
- CORS currently permits all origins for local development. Use an explicit origin allowlist before deploying publicly.
