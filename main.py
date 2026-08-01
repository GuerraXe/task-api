from fastapi import FastAPI, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

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
def create_task(task: TaskCreate):
    pass


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks():
    pass


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskCreate):
    pass


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    pass


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
