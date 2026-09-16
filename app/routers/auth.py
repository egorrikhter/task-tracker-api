from typing import Annotated

from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from schemas import UserCreate, UserRead
from security import hash_password
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserRead)
async def register_user(
    user_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]
):
    email = user_data.email
    username = user_data.username
    password = hash_password(user_data.password)
    user = User(email=email, username=username, password_hash=password)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Username or email already exists.")

    return user
