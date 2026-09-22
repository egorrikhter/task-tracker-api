import datetime
from os import getenv
from uuid import UUID, uuid4

import jwt
from bcrypt import checkpw, gensalt, hashpw
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

SECRET_KEY = getenv("SECRET_KEY")

credentials_exception = HTTPException(
    status_code=401,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
)


def hash_password(password: str) -> str:
    bytes_pass = password.encode("utf-8")
    salt = gensalt()
    hash_pass = hashpw(bytes_pass, salt)
    return hash_pass.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def encode_string(payload, minutes):
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
        minutes=minutes
    )
    token = jwt.encode(payload_copy, SECRET_KEY, algorithm="HS256")
    return token


def create_access_token(user_id):

    payload = {"sub": str(user_id), "jti": str(uuid4()), "type": "access"}
    token = encode_string(payload, 15)
    return token


def create_refresh_token(user_id):
    payload = {"sub": str(user_id), "jti": str(uuid4()), "type": "refresh"}
    token = encode_string(payload, 10800)
    return token


def access_refresh_resp(user_id):
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def get_user_id(user_id_str: str | None) -> UUID:

    if not user_id_str:
        raise credentials_exception

    try:
        return UUID(user_id_str)

    except ValueError:
        raise credentials_exception


def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
