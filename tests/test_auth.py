from datetime import datetime_CAPI

from httpx import AsyncClient
from sqlalchemy.sql import select

from app.models import User


async def test_register(async_client: AsyncClient, db_session):

    email = "testmail@gmail.com"
    username = "testusername"
    password = "testpassword"

    response = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == "testmail@gmail.com"
    assert data["username"] == "testusername"

    user = await db_session.scalar(select(User).where(User.email == email))

    assert user is not None
    assert user.password_hash != password


async def test_register_email_exists(async_client: AsyncClient, sample_user):

    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    response = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    assert response.status_code == 409


async def test_register_invalid_data(async_client: AsyncClient):

    email = "testtest.com"
    username = "ui"
    password = "password"

    response = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    assert response.status_code == 422


async def test_login(async_client: AsyncClient):

    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    create_user = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    response = await async_client.post(
        "/auth/login",
        json={"email": email, "username": username, "password": password},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


async def test_login_invalid_email(async_client: AsyncClient):

    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    create_user = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    response = await async_client.post(
        "/auth/login",
        json={
            "email": "test_test@test.com",
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 401


async def test_login_invalid_password(async_client: AsyncClient):

    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    create_user = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    response = await async_client.post(
        "/auth/login",
        json={
            "email": email,
            "username": username,
            "password": "testtpassword",
        },
    )

    assert response.status_code == 401


async def test_refresh(async_client: AsyncClient):

    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    create_user = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    login_user = await async_client.post(
        "/auth/login",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    data = login_user.json()
    refresh_token = data["refresh_token"]

    response = await async_client.post(
        "/auth/refresh", json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200


async def test_access_instead_refresh(async_client: AsyncClient):
    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    create_user = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    login_user = await async_client.post(
        "/auth/login",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    data = login_user.json()
    access_token = data["access_token"]

    response = await async_client.post(
        "/auth/refresh", json={"refresh_token": access_token}
    )

    assert response.status_code == 401


async def test_invalid_token(async_client: AsyncClient):

    email = "test@test.com"
    username = "testusername"
    password = "testpassword"

    create_user = await async_client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    login_user = await async_client.post(
        "/auth/login",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    response = await async_client.post(
        "/auth/refresh",
        json={"refresh_token": "some string"},
    )

    assert response.status_code == 401
