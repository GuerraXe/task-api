from fastapi import FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI()


class TaskInput(BaseModel):
    title: str
    hours: float


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


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskInput):
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

    return {"title": task.title, "hours": task.hours}


if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
