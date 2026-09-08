from os import getenv

from dotenv import load_dotenv
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv()


class Base(DeclarativeBase):
    pass


url_object = URL.create(
    "postgresql+asyncpg",
    username=getenv("POSTGRES_USER"),
    password=getenv("POSTGRES_PASSWORD"),
    port=int(getenv("POSTGRES_PORT", "5432")),
    database=getenv("POSTGRES_DB"),
    host=getenv("POSTGRES_HOST", "localhost"),
)

engine = create_async_engine(url_object, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
