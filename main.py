import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from db import get_db, init_db

app = FastAPI()

# Module 3: permissive CORS is limited to local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TaskCreate(BaseModel):
    title: str
    hours: float


class TaskResponse(TaskCreate):
    id: int


def validate_task_values(task: TaskCreate) -> None:
    if not task.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Title must not be empty",
        )
    if task.hours < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hours must not be negative",
        )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    _request, exc: RequestValidationError
) -> JSONResponse:
    # Invalid JSON, missing keys, and incompatible types are client errors.
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


@app.get("/")
def read_root():
    return {"status": "online"}


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    task: TaskCreate,
    connection: sqlite3.Connection = Depends(get_db),
):
    validate_task_values(task)
    cursor = connection.execute(
        "INSERT INTO tasks (title, hours) VALUES (?, ?)",
        (task.title, task.hours),
    )
    connection.commit()

    task_id = cursor.lastrowid
    if task_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task ID was not generated",
        )

    row = connection.execute(
        "SELECT id, title, hours FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Created task could not be loaded",
        )
    return dict(row)


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(connection: sqlite3.Connection = Depends(get_db)):
    rows = connection.execute(
        "SELECT id, title, hours FROM tasks ORDER BY id"
    ).fetchall()
    return [dict(row) for row in rows]


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task: TaskCreate,
    connection: sqlite3.Connection = Depends(get_db),
):
    validate_task_values(task)
    cursor = connection.execute(
        "UPDATE tasks SET title = ?, hours = ? WHERE id = ?",
        (task.title, task.hours, task_id),
    )
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    connection.commit()

    row = connection.execute(
        "SELECT id, title, hours FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Updated task could not be loaded",
        )
    return dict(row)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    connection: sqlite3.Connection = Depends(get_db),
) -> Response:
    cursor = connection.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,),
    )
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    connection.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    init_db()
    uvicorn.run("main:app", port=8000, reload=True)
