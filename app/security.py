import datetime
import uuid
from os import getenv

import jwt
from bcrypt import checkpw, gensalt, hashpw
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

SECRET_KEY = getenv("SECRET_KEY")


def hash_password(password: str) -> str:
    bytes_pass = password.encode("utf-8")
    salt = gensalt()
    hash_pass = hashpw(bytes_pass, salt)
    return hash_pass.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(id):
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(id),
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=10),
        "jwt": str(uuid.uuid4()),
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256", headers=header)
    response = {"access_token": access_token, "token_type": "bearer"}
    return response


def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="The token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="The token is invalid.")
