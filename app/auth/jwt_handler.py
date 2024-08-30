import time
from datetime import datetime

from fastapi import HTTPException
from starlette import status

from app.config import Setting
from jose import jwt, JWTError

settings = Setting()


def create_access_token(user: dict):
    payload = {
        "user": user
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token


def verify_access_token(token: str):
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return data
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )



