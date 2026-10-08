from uuid import uuid4

from httpx import AsyncClient

from app.dependencies import get_current_user  # Проверь правильность пути импорта
from app.main import app


async def test_patch_task_clear_tags(
    async_client: AsyncClient, sample_task, sample_user
):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.patch(f"/tasks/{sample_task.id}", json={"tags": []})

    assert response.status_code == 200
    data = response.json()
    assert data["tags"] == []


async def test_patch_task_incorrent_id(async_client: AsyncClient, sample_user):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    task_id = uuid4()

    response = await async_client.patch(f"/tasks/{task_id}", json={"title": "NewTitle"})
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "The requested resource could not be found."


async def test_patch_task_incorrect_payload(
    async_client: AsyncClient, sample_user, sample_task
):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.patch(
        f"/tasks/{sample_task.id}", json={"title": "hr"}
    )
    assert response.status_code == 422


async def test_post_task(async_client: AsyncClient, sample_user, sample_project):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.post(
        "/tasks",
        json={"title": "NewTitle", "project_id": str(sample_project.id)},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["title"] == "NewTitle"


async def test_post_empty_json(async_client: AsyncClient, sample_user):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.post("/tasks", json={})
    assert response.status_code == 422


async def test_post_defunct_project(async_client: AsyncClient, sample_user):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.post(
        "/tasks", json={"title": "NewTitle", "project_id": str(uuid4())}
    )
    assert response.status_code == 404


async def test_get_task(async_client: AsyncClient, sample_user, sample_task):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get(f"/tasks/{sample_task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_task.id)
    assert data["title"] == sample_task.title
    assert data["project_id"] == str(sample_task.project_id)


async def test_get_defunct_task(async_client: AsyncClient, sample_user):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get(f"/tasks/{uuid4()}")
    assert response.status_code == 404


async def test_get_tasks(async_client: AsyncClient, sample_user, sample_task):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(task["id"] == str(sample_task.id) for task in data)


async def test_delete_task(async_client: AsyncClient, sample_user, sample_task):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.delete(f"/tasks/{sample_task.id}")
    assert response.status_code == 204
    get_response = await async_client.get(f"/tasks/{sample_task.id}")
    assert get_response.status_code == 404


async def test_delete_defunct_task(async_client: AsyncClient, sample_user):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.delete(f"/tasks/{uuid4()}")
    assert response.status_code == 404


async def test_change_strange_task_title(
    async_client: AsyncClient, another_user, sample_task
):
    app.dependency_overrides[get_current_user] = lambda: another_user

    response = await async_client.patch(
        f"/tasks/{sample_task.id}", json={"title": "ChangeTitle"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "The requested resource could not be found."


async def test_change_strange_task_assignee_id(
    async_client: AsyncClient, sample_user, another_user, sample_task
):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.patch(
        f"/tasks/{sample_task.id}", json={"assignee_id": str(another_user.id)}
    )
    print(response.json()["detail"])
    assert response.status_code == 400


async def test_delete_strange_task(
    async_client: AsyncClient, another_user, sample_task
):
    app.dependency_overrides[get_current_user] = lambda: another_user

    response = await async_client.delete(f"/tasks/{sample_task.id}")
    assert response.status_code == 404
