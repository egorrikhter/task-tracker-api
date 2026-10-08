import os
from collections.abc import AsyncGenerator

import httpx
import pytest
from dotenv import load_dotenv
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text

from app.database import Base, get_db
from app.main import app
from app.models import Project, Task, User

load_dotenv()
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/tracker_test",
)
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True, scope="session")
async def prepare_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(
                text(f"TRUNCATE {table.name} RESTART IDENTITY CASCADE;")
            )
        await session.commit()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def sample_user(db_session):
    user = User(email="test@test.com", username="test", password_hash="test")
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
async def sample_task(db_session, sample_user):
    project = Project(title="test", owner_id=sample_user.id)
    db_session.add(project)
    await db_session.flush()

    task = Task(
        title="test",
        project_id=project.id,
        creator_id=sample_user.id,
        assignee_id=sample_user.id,
    )
    db_session.add(task)
    await db_session.commit()
    return task


@pytest.fixture
async def sample_project(db_session, sample_user):
    project = Project(title="test", owner_id=sample_user.id)
    db_session.add(project)
    await db_session.commit()
    return project


@pytest.fixture
async def another_user(db_session):
    user = User(email="test2@test@.com", username="test2", password_hash="test2")
    db_session.add(user)
    await db_session.commit()
    return user
