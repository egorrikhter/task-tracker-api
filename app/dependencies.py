from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.security import get_user_id, verify_token

security = HTTPBearer()
credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
):

    token = credentials.credentials

    payload = verify_token(token)
    if payload.get("type") != "access":
        raise credentials_exception

    user_id_str = payload.get("sub")

    user_id = get_user_id(user_id_str)

    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise credentials_exception
    return user
