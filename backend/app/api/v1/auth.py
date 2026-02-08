from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.db.mongo import get_auth_db
from app.schemas.auth import SignUpIn, SignInIn, TokenOut
from app.services.auth_service import create_user, get_user_by_email, check_password
from app.core.security import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def auth_db_dep():
    return get_auth_db

@router.post("/signup", response_model=TokenOut, status_code=201)
async def signup(payload: SignUpIn, auth_db: AsyncIOMotorDatabase = Depends(auth_db_dep())):
    try:
        await create_user(auth_db, payload.email, payload.password)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Email already registered")

    token = create_access_token(subject=payload.email.lower())
    return TokenOut(access_token=token)

@router.post("/signin", response_model=TokenOut)
async def signin(payload: SignInIn, auth_db: AsyncIOMotorDatabase = Depends(auth_db_dep())):
    user = await get_user_by_email(auth_db, payload.email)
    if not user or not check_password(user, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user["email"])
    return TokenOut(access_token=token)
