from bcrypt import checkpw, gensalt, hashpw


def hash_password(password: str) -> str:
    bytes_pass = password.encode("utf-8")
    salt = gensalt()
    hash_pass = hashpw(bytes_pass, salt)
    return hash_pass.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
