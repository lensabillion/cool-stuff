from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.common.mongo import now_utc
from app.common.utils import Role
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth import repository
from app.modules.auth.schemas import LoginRequest, SignupRequest, TokenResponse


async def signup(payload: SignupRequest) -> TokenResponse:
    user_doc = {
        "username": payload.username,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "role": Role.user.value,
        "created_at": now_utc(),
    }
    try:
        result = await repository.create_user(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Username or email already used")
    user_doc["_id"] = result.inserted_id
    return TokenResponse(access_token=create_access_token(user_doc))


async def login(payload: LoginRequest) -> TokenResponse:
    user = await repository.find_by_username_or_email(payload.username_or_email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user))
