from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import auth_db
from app.core.security import hash_password, verify_password, create_access_token

async def signup_user(username: str, email: str, password: str) -> dict:
    # 1) ensure username/email not taken
    existing = await auth_db.users.find_one({"$or": [{"username": username}, {"email": email}]})
    if existing:
        # return a clean error later from router (409)
        raise ValueError("Username or email already exists")

    # 2) hash password
    print("DEBUG password repr:", repr(password))
    print("DEBUG password length:", len(password))

    password_hash = hash_password(password)

    # 3) insert user
    doc = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": "user",
        "created_at": datetime.now(timezone.utc),
    }
    result = await auth_db.users.insert_one(doc)

    # 4) return safe user shape
    return {
        "id": str(result.inserted_id),
        "username": username,
        "email": email,
        "role": "user",
    }

async def login_user(email: str, password: str) -> dict:
    user = await auth_db.users.find_one({"email": email})
    if not user:
        raise ValueError("Invalid credentials")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid credentials")

    token = create_access_token(
        sub=str(user["_id"]),
        role=user.get("role", "user"),
        username=user["username"],
    )
    return {"access_token": token, "token_type": "bearer"}
