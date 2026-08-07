"""
Security utilities: password hashing, JWT creation/validation.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.schemas import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_token(subject: str, role: str, expires_delta: timedelta, token_type: str = "access") -> str:
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": subject, "role": role, "exp": expire, "type": token_type}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    return create_token(subject, role, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access")


def create_refresh_token(subject: str, role: str) -> str:
    return create_token(subject, role, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh")


def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    return decode_token(token)


def require_role(*allowed_roles: str):
    async def role_checker(payload: TokenPayload = Depends(get_current_token_payload)):
        if payload.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return payload
    return role_checker
