from uuid import uuid4

from httpx import AsyncClient

from app.dependencies import get_current_user
from app.main import app


async def test_project_create(async_client: AsyncClient, sample_user):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.post("/projects", json={"title": "NewTitle"})

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "NewTitle"
    assert "id" in data


async def test_get_projects(async_client: AsyncClient, sample_user, sample_project):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get("/projects")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["id"] == str(sample_project.id)


async def test_get_project(async_client: AsyncClient, sample_user, sample_project):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get(f"/projects/{sample_project.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_project.id)
    assert data["title"] == "test"


async def test_get_defunct_project(async_client: AsyncClient, sample_user):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.get(f"/projects/{uuid4()}")

    assert response.status_code == 404


async def test_patch_project(async_client: AsyncClient, sample_user, sample_project):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.patch(
        f"/projects/{sample_project.id}", json={"title": "NewTitle"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_project.id)
    assert data["title"] == "NewTitle"
    assert data["owner_id"] == str(sample_user.id)


async def test_patch_strange_project(
    async_client: AsyncClient, sample_user, sample_project, another_user
):

    app.dependency_overrides[get_current_user] = lambda: another_user

    response = await async_client.patch(
        f"/projects/{sample_project.id}", json={"title": "NewTitle"}
    )

    assert response.status_code == 404


async def test_get_strange_project(
    async_client: AsyncClient, sample_user, another_user, sample_project
):

    app.dependency_overrides[get_current_user] = lambda: another_user

    response = await async_client.get(f"/projects/{sample_project.id}")

    assert response.status_code == 404


async def test_delete_project(async_client: AsyncClient, sample_user, sample_project):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.delete(f"/projects/{sample_project.id}")

    assert response.status_code == 204
    get_response = await async_client.get(f"/projects/{sample_project.id}")
    assert get_response.status_code == 404


async def test_delete_strange_project(
    async_client: AsyncClient, sample_user, another_user, sample_project
):

    app.dependency_overrides[get_current_user] = lambda: another_user

    response = await async_client.delete(f"/projects/{sample_project.id}")

    assert response.status_code == 404


async def test_delete_defunct_project(async_client: AsyncClient, sample_user):

    app.dependency_overrides[get_current_user] = lambda: sample_user

    response = await async_client.delete(f"/projects/{uuid4()}")

    assert response.status_code == 404
