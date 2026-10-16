from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.dependencies import get_current_user
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
    assert any(task["id"] == str(sample_task.id) for task in data["items"])


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


async def test_patch_tags(async_client: AsyncClient, sample_user, sample_task):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.patch(
        f"/tasks/{sample_task.id}", json={"tags": ["backend", "testing"]}
    )

    assert response.status_code == 200
    data = response.json()
    tag_names = {tag["name"] for tag in data["tags"]}
    assert tag_names == {"backend", "testing"}


async def test_unique_tasks(async_client: AsyncClient, sample_user, sample_project):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    task_a_title = "Task_A"
    task_b_title = "Task_b"

    create_task_a = await async_client.post(
        "/tasks", json={"title": task_a_title, "project_id": str(sample_project.id)}
    )
    create_task_b = await async_client.post(
        "/tasks", json={"title": task_b_title, "project_id": str(sample_project.id)}
    )
    task_a_id = str(create_task_a.json()["id"])
    response = await async_client.patch(
        f"/tasks/{task_a_id}", json={"title": task_b_title}
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "invalid_params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"order": "unknown"}],
)
async def test_limit(async_client: AsyncClient, sample_user, invalid_params):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get("/tasks", params=invalid_params)

    assert response.status_code == 422


async def test_pagination(async_client: AsyncClient, sample_user, sample_project):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    for i in range(1, 5):
        res = await async_client.post(
            "/tasks", json={"title": f"Task{i}", "project_id": str(sample_project.id)}
        )

    first_response = await async_client.get(
        "/tasks",
        params={"limit": 2, "offset": 0},
    )

    assert first_response.status_code == 200
    first_data = first_response.json()
    assert first_data["total"] == 4
    assert len(first_data["items"]) == 2

    second_response = await async_client.get("/tasks", params={"limit": 2, "offset": 2})
    assert second_response.status_code == 200
    second_data = second_response.json()
    first_ids = {task["id"] for task in first_data["items"]}
    second_ids = {task["id"] for task in second_data["items"]}
    assert first_ids.isdisjoint(second_ids)

    assert len(first_data | second_data) == 4


async def test_filtration(async_client: AsyncClient, sample_user, sample_project):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    first_task = await async_client.post(
        "/tasks",
        json={"title": "TodoTask", "project_id": str(sample_project.id)},
    )
    assert first_task.status_code == 201

    second_task = await async_client.post(
        "/tasks",
        json={"title": "DoneTask", "project_id": str(sample_project.id)},
    )
    assert second_task.status_code == 201

    first_task_id = first_task.json()["id"]

    # Обновляем статус и навешиваем тег через PATCH
    patch_res = await async_client.patch(
        f"/tasks/{first_task_id}",
        json={"status": "done", "tags": ["backend"]},
    )
    assert patch_res.status_code == 200

    # Фильтрация по статусу
    get_status = await async_client.get("/tasks", params={"status": "done"})
    assert get_status.status_code == 200
    status_data = get_status.json()
    assert status_data["total"] == 1
    assert len(status_data["items"]) == 1
    assert status_data["items"][0]["status"] == "done"

    # Фильтрация по тегу
    get_tags = await async_client.get("/tasks", params={"tag": "backend"})
    assert get_tags.status_code == 200
    tags_data = get_tags.json()
    assert tags_data["total"] == 1
    assert len(tags_data["items"]) == 1
    assert any(t["name"] == "backend" for t in tags_data["items"][0]["tags"])


async def test_sorting(async_client: AsyncClient, sample_user, sample_project):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    for i in range(1, 5):
        res = await async_client.post(
            "/tasks", json={"title": f"Task{i}", "project_id": str(sample_project.id)}
        )
        assert res.status_code == 201

    res_desc = await async_client.get("/tasks", params={"order": "desc"})
    assert res_desc.status_code == 200

    desc_data = res_desc.json()

    res_asc = await async_client.get("/tasks", params={"order": "asc"})
    assert res_asc.status_code == 200

    asc_data = res_asc.json()

    desc_ids = [task["id"] for task in desc_data["items"]]
    asc_ids = [task["id"] for task in asc_data["items"]]
    assert desc_ids == list(reversed(asc_ids))


async def test_task_enqueued_on_creation(
    async_client: AsyncClient, sample_user, sample_project, mock_arq_redis
):
    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.post(
        "/tasks",
        json={"title": "Redis Task", "project_id": str(sample_project.id)},
    )
    assert response.status_code == 201

    mock_arq_redis.enqueue_job.assert_awaited_once_with(
        "notify_task_created",
        email=sample_user.email,
        task_title="Redis Task",
    )
