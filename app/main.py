import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(auth_router)
app.include_router(tasks_router)


@app.exception_handler(Exception)
async def handle_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unexpected processing failure: %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )

    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
