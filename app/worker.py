import asyncio
import os
from typing import Any

from arq.connections import RedisSettings
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


async def notify_task_created(ctx: dict[str, Any], email: str, task_title: str) -> str:
    print(f"\n[WORKER] The creation of a task named {task_title} was intercepted.")
    await asyncio.sleep(3)
    print(f"\n[WORKER] The work is complete {email}")
    return f"Done {email}"


class WorkerSettings:
    functions = (notify_task_created,)
    redis_settings = RedisSettings(host=REDIS_HOST, port=REDIS_PORT)
