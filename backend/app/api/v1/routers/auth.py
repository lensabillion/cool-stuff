import time

from fastapi import APIRouter, HTTPException, Depends, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import SignupIn, LoginIn, TokenOut, UserOut
from app.services.auth_service import signup_user, login_user
from app.core.dependencies import get_current_user
from app.core.redis_client import redis_client
from app.core.security import decode_access_token
from app.core.rate_limit import rate_limit, get_client_ip
from app.core.rate_limit_rules import RULES

from fastapi import Request
router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer()

@router.post("/logout", status_code=204)
async def logout(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
):
    token = creds.credentials

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        raise HTTPException(status_code=400, detail="Token missing jti/exp")

    ttl = max(1, int(exp - time.time()))
    await redis_client.setex(f"bl:{jti}", ttl, "1")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/signup", response_model=UserOut, status_code=201)
async def signup(payload: SignupIn, request: Request):
    ip = get_client_ip(request)
    limit, window = RULES["auth:signup_ip"]
    await rate_limit(key=f"auth:signup:ip:{ip}", limit=limit, window_seconds=window)

    try:
        return await signup_user(payload.username, payload.email, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request):
    ip = get_client_ip(request)
    limit, window = RULES["auth:login_ip"]
    await rate_limit(key=f"auth:login:ip:{ip}", limit=limit, window_seconds=window)

    email = payload.email.strip().lower()
    limit, window = RULES["auth:login_email"]
    await rate_limit(key=f"auth:login:email:{email}", limit=limit, window_seconds=window)

    try:
        return await login_user(payload.email, payload.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/me", response_model=UserOut)
async def me(current_user=Depends(get_current_user)):
    return current_user
