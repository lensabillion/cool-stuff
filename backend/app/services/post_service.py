from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import app_db

async def create_post(topic_id: str, body: str, current_user: dict) -> dict:
    # ensure topic exists
    topic = await app_db.topics.find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise ValueError("Topic not found")
        
     # Admin can post anywhere without subscribing
    if current_user.get("role") != "admin":
        sub = await app_db.subscriptions.find_one({
            "topic_id": ObjectId(topic_id),
            "user_id": ObjectId(current_user["id"]),
        })
        if not sub:
            raise PermissionError("Must be subscribed to post in this topic")
    now = datetime.now(timezone.utc)
    doc = {
        "topic_id": ObjectId(topic_id),
        "created_by": ObjectId(current_user["id"]),
        "body": body,
        "created_at": now,
        "updated_at": None,
        "upvote_count": 0,
        "comment_count": 0,
    }
    res = await app_db.posts.insert_one(doc)

    # optional: update topic post_count if you want
    await app_db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {"$inc": {"post_count": 1}}
    )

    return {
        "id": str(res.inserted_id),
        "topic_id": topic_id,
        "created_by": current_user["id"],
        "body": body,
        "created_at": now,
        "updated_at": None,
        "upvote_count": 0,
        "comment_count": 0,
    }

async def list_posts_by_topic(topic_id: str, limit: int = 20, skip: int = 0) -> list[dict]:
    cursor = (
        app_db.posts.find({"topic_id": ObjectId(topic_id)})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    posts = []
    async for p in cursor:
        posts.append({
            "id": str(p["_id"]),
            "topic_id": str(p["topic_id"]),
            "created_by": str(p["created_by"]),
            "body": p["body"],
            "created_at": p["created_at"],
            "updated_at": p.get("updated_at"),
            "upvote_count": p.get("upvote_count", 0),
            "comment_count": p.get("comment_count", 0),
        })
    return posts

async def update_post(post_id: str, body: str, current_user: dict) -> dict:
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(post["created_by"]) == current_user["id"]
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to edit this post")

    now = datetime.now(timezone.utc)
    await app_db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"body": body, "updated_at": now}}
    )

    # return updated shape
    return {
        "id": post_id,
        "topic_id": str(post["topic_id"]),
        "created_by": str(post["created_by"]),
        "body": body,
        "created_at": post["created_at"],
        "updated_at": now,
        "upvote_count": post.get("upvote_count", 0),
        "comment_count": post.get("comment_count", 0),
    }

async def delete_post(post_id: str, current_user: dict) -> None:
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(post["created_by"]) == current_user["id"]
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to delete this post")

    # delete related data
    await app_db.comments.delete_many({"post_id": ObjectId(post_id)})
    await app_db.upvotes.delete_many({"post_id": ObjectId(post_id)})
    await app_db.bookmarks.delete_many({"post_id": ObjectId(post_id)})

    await app_db.posts.delete_one({"_id": ObjectId(post_id)})

    # update topic post_count if you track it
    await app_db.topics.update_one(
        {"_id": post["topic_id"]},
        {"$inc": {"post_count": -1}}
    )
