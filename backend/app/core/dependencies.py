import jwt
from fastapi import Depends, Header, HTTPException

from app.common.mongo import to_object_id
from app.common.utils import Role
from app.core.database import get_auth_db
from app.core.security import decode_access_token
from app.modules.auth.schemas import CurrentUser


async def get_current_user(authorization: str = Header(default="")) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await get_auth_db().users.find_one({"_id": to_object_id(payload["sub"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return CurrentUser(id=str(user["_id"]), username=user["username"], email=user["email"], role=user["role"])


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
