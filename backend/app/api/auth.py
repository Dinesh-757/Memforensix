"""
Authentication endpoints: register, login, refresh, current user.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import User, get_db
from app.models.schemas import Token, UserCreate, UserLogin, UserOut
from app.utils.security import (create_access_token, create_refresh_token,
                                 get_current_token_payload, hash_password,
                                 verify_password)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.username == payload.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    from datetime import datetime
    user.last_login = datetime.utcnow()
    await db.commit()

    return Token(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id, user.role.value),
    )


@router.get("/me", response_model=UserOut)
async def get_me(payload=Depends(get_current_token_payload), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
