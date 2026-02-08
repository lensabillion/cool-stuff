from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
from app.core.security import hash_password, verify_password

USERS_COL = "users"

async def ensure_auth_indexes(auth_db: AsyncIOMotorDatabase) -> None:
    await auth_db[USERS_COL].create_index([("email", ASCENDING)], unique=True)

async def create_user(auth_db: AsyncIOMotorDatabase, email: str, password: str) -> dict:
    doc = {
        "email": email.lower(),
        "hashed_password": hash_password(password),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    res = await auth_db[USERS_COL].insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc

async def get_user_by_email(auth_db: AsyncIOMotorDatabase, email: str) -> dict | None:
    return await auth_db[USERS_COL].find_one({"email": email.lower()})

def check_password(user: dict, password: str) -> bool:
    return verify_password(password, user["hashed_password"])
