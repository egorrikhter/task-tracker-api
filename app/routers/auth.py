import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import TokenRefresh, TokenResponse, UserCreate, UserLogin, UserRead
from app.security import (
    access_refresh_resp,
    get_user_id,
    hash_password,
    verify_password,
    verify_token,
)

load_dotenv()
router = APIRouter()
DUMMY_HASH = os.getenv("DUMMY_HASH")
credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
)


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
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user and user.password_hash:
        target_hash = user.password_hash
    else:
        target_hash = DUMMY_HASH

    is_valid = verify_password(password, str(target_hash))

    if user and is_valid:
        tokens = access_refresh_resp(user.id)
        return tokens
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials.")


@router.post("/refresh", response_model=TokenResponse)
async def token_refresh(
    refresh_token: TokenRefresh, db: Annotated[AsyncSession, Depends(get_db)]
):
    payload = verify_token(refresh_token.refresh_token)

    if payload.get("type") != "refresh":
        raise credentials_exception

    user_id_str = payload.get("sub")

    user_id = get_user_id(user_id_str)

    user = (
        await db.execute(select(User).where(User.id == user_id))
    ).scalar_one_or_none()

    if not user:
        raise credentials_exception

    tokens = access_refresh_resp(user_id)
    return tokens


@router.get("/me")
async def read_current_user(current_user: Annotated[User, Depends(get_current_user)]):
    return {"id": current_user.id, "email": current_user.email}
