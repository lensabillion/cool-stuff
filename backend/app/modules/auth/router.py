from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUser, LoginRequest, SignupRequest, TokenResponse
from app.modules.auth.service import login, signup

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
async def signup_route(payload: SignupRequest) -> TokenResponse:
    return await signup(payload)


@router.post("/login", response_model=TokenResponse)
async def login_route(payload: LoginRequest) -> TokenResponse:
    return await login(payload)


@router.get("/me", response_model=CurrentUser)
async def me_route(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user
