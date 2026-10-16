import logging
import os
from contextlib import asynccontextmanager

from arq import create_pool
from arq.connections import RedisSettings
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_redis = await create_pool(
        RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
    )

    yield

    await app.state.arq_redis.close()


app = FastAPI(title="Task Tracker API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(projects_router)


@app.exception_handler(Exception)
async def handle_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unexpected processing failure: %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )

    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
