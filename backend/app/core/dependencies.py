from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.core.database import auth_db
from app.core.security import decode_access_token
from app.core.redis_client import redis_client
bearer = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
):
    token = creds.credentials

    try:
        payload = decode_access_token(token)
        user_id = payload["sub"]
        jti = payload.get("jti")
        if jti:
            if await redis_client.get(f"bl:{jti}"):
                raise HTTPException(status_code=401, detail="Token revoked")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await auth_db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # never leak password hash
    user["id"] = str(user["_id"])
    user.pop("password_hash", None)
    return user

def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
