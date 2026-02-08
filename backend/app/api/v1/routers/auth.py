from fastapi import APIRouter, HTTPException, Depends

from app.schemas.auth import SignupIn, LoginIn, TokenOut, UserOut
from app.services.auth_service import signup_user, login_user
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(payload: SignupIn):
    try:
        return await signup_user(payload.username, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn):
    try:
        return await login_user(payload.email, payload.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
