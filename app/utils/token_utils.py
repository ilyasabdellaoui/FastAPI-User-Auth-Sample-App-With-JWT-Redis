import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Any, Union

import jwt
from jose import jwt

from fastapi import Depends
from passlib.context import CryptContext
from app.config.settings import (ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM,
                        REFRESH_TOKEN_EXPIRE_MINUTES)
from app.utils.jwt_utils import JWTBearer

load_dotenv()
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
JWT_REFRESH_SECRET_KEY = os.environ.get("JWT_REFRESH_SECRET_KEY")

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str):
    return password_context.hash(password)

def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)

def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt

def get_authenticated_user_id(token: str = Depends(JWTBearer())) -> int:
    payload = jwt.decode(token, JWT_SECRET_KEY, ALGORITHM)
    authenticated_user_id = int(payload['sub'])
    return authenticated_user_id