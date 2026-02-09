from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError
from app.core.database import auth_db
from app.core.security import hash_password, verify_password, create_access_token

async def signup_user(username: str, email: str, password: str) -> dict:
    username = username.strip()
    email = email.strip().lower()

    doc = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "role": "user",
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = await auth_db.users.insert_one(doc)
    except DuplicateKeyError:
        raise ValueError("Username or email already exists")

    return {
        "id": str(result.inserted_id),
        "username": username,
        "email": email,
        "role": "user",
    }

async def login_user(email: str, password: str) -> dict:
    email = email.strip().lower()

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
