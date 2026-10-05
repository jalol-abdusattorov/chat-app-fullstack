import os
import jwt
from dotenv import load_dotenv, find_dotenv
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status

from auth.models.token import TokenData
from auth.utils.auth_utils import verify_password
from db import users_collection

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def authenticate_user(email: str, password: str):
    user = users_collection.find_one({ "email": email })
    if not user:
        return False
    if not verify_password(password, user['password_hash']):
        return False

    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({ "exp": expire })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt