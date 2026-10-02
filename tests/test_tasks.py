import pytest
from httpx import AsyncClient

from app.dependencies import get_current_user  # Проверь правильность пути импорта
from app.main import app


async def test_patch_task_clear_tags(
    async_client: AsyncClient, sample_task, sample_user
):
    # ==========================================
    # 1. ARRANGE
    # ==========================================
    # База уже заполнена благодаря фикстурам.
    # Просто говорим приложению считать sample_user авторизованным:
    app.dependency_overrides[get_current_user] = lambda: sample_user

    # ==========================================
    # 2. ACT
    # ==========================================
    response = await async_client.patch(f"/tasks/{sample_task.id}", json={"tags": []})

    # ==========================================
    # 3. ASSERT
    # ==========================================
    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == []
