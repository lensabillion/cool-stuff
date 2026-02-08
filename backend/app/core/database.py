from pathlib import Path
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.core.config import settings

mongo_client: Optional[AsyncIOMotorClient] = None
auth_db: Optional[AsyncIOMotorDatabase] = None
app_db: Optional[AsyncIOMotorDatabase] = None


async def connect_db() -> None:
    global mongo_client, auth_db, app_db
    mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    auth_db = mongo_client[settings.auth_db_name]
    app_db = mongo_client[settings.app_db_name]

    await auth_db.users.create_index("username", unique=True)
    await auth_db.users.create_index("email", unique=True)

    await app_db.topics.create_index([("name", "text"), ("description", "text")])
    await app_db.subscriptions.create_index([("user_id", ASCENDING), ("topic_id", ASCENDING)], unique=True)
    await app_db.posts.create_index("topic_id")
    await app_db.posts.create_index([("created_at", DESCENDING)])
    await app_db.comments.create_index("post_id")
    await app_db.upvotes.create_index([("user_id", ASCENDING), ("post_id", ASCENDING)], unique=True)
    await app_db.bookmarks.create_index([("user_id", ASCENDING), ("post_id", ASCENDING)], unique=True)

    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


def close_db() -> None:
    if mongo_client:
        mongo_client.close()


def get_auth_db() -> AsyncIOMotorDatabase:
    if auth_db is None:
        raise RuntimeError("auth_db not initialized")
    return auth_db


def get_app_db() -> AsyncIOMotorDatabase:
    if app_db is None:
        raise RuntimeError("app_db not initialized")
    return app_db
