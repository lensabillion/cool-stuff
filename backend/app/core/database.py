from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)

# Two separate Mongo databases (same server)
auth_db = client[settings.MONGO_AUTH_DB]
app_db = client[settings.MONGO_APP_DB]
async def ensure_indexes():
    # AUTH DB
    await auth_db.users.create_index("email", unique=True)
    await auth_db.users.create_index("username", unique=True)

    # APP DB
    await app_db.topics.create_index("name", unique=True)

    await app_db.subscriptions.create_index(
        [("user_id", 1), ("topic_id", 1)],
        unique=True
    )

    await app_db.upvotes.create_index(
        [("user_id", 1), ("post_id", 1)],
        unique=True
    )

    await app_db.bookmarks.create_index(
        [("user_id", 1), ("post_id", 1)],
        unique=True
    )