from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import app_db

async def upvote_post(post_id: str, current_user: dict) -> None:
    # ensure post exists
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")

    # idempotent: if already upvoted, do nothing
    existing = await app_db.upvotes.find_one({
        "post_id": ObjectId(post_id),
        "user_id": ObjectId(current_user["id"]),
    })
    if existing:
        return

    await app_db.upvotes.insert_one({
        "post_id": ObjectId(post_id),
        "user_id": ObjectId(current_user["id"]),
        "created_at": datetime.now(timezone.utc),
    })

    # increment counter on post
    await app_db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$inc": {"upvote_count": 1}}
    )

async def remove_upvote(post_id: str, current_user: dict) -> None:
    # idempotent: if not upvoted, do nothing
    res = await app_db.upvotes.delete_one({
        "post_id": ObjectId(post_id),
        "user_id": ObjectId(current_user["id"]),
    })

    if res.deleted_count == 1:
        await app_db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$inc": {"upvote_count": -1}}
        )
