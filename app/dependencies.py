from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User
from app.security import verify_token

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token = credentials.credentials

    payload = verify_token(token)
    user = await db.scalar(select(User).where(User.id == payload.get("sub")))

    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
