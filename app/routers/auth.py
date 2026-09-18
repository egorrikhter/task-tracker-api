from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TokenResponse, UserCreate, UserLogin, UserRead
from app.security import create_access_token, hash_password, verify_password

router = APIRouter()


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


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]
):
    email = user_data.email
    password = user_data.password
    id = await db.scalar(select(User.id).where(User.email == email))
    password_hash = await db.scalar(
        select(User.password_hash).where(User.email == email)
    )
    if password_hash is not None:
        if verify_password(password, password_hash):
            access_token = create_access_token(id)
        else:
            raise HTTPException(status_code=401, detail="The password is incorrect")
    else:
        raise HTTPException(status_code=401, detail="The email address is incorrect.")
    return access_token


@router.get("/me")
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return {"id": current_user.id, "email": current_user.email}
