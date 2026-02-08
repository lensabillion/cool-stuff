from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import app_db

async def bookmark_post(post_id: str, current_user: dict) -> None:
    # ensure post exists
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")

    existing = await app_db.bookmarks.find_one({
        "post_id": ObjectId(post_id),
        "user_id": ObjectId(current_user["id"]),
    })
    if existing:
        return

    await app_db.bookmarks.insert_one({
        "post_id": ObjectId(post_id),
        "user_id": ObjectId(current_user["id"]),
        "created_at": datetime.now(timezone.utc),
    })

async def unbookmark_post(post_id: str, current_user: dict) -> None:
    await app_db.bookmarks.delete_one({
        "post_id": ObjectId(post_id),
        "user_id": ObjectId(current_user["id"]),
    })

async def list_my_bookmarks(current_user: dict, limit: int = 50, skip: int = 0) -> list[dict]:
    # get bookmarks newest-first
    cursor = (
        app_db.bookmarks.find({"user_id": ObjectId(current_user["id"])})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    post_ids = []
    async for b in cursor:
        post_ids.append(b["post_id"])

    if not post_ids:
        return []

    # fetch posts for those ids
    posts_cursor = app_db.posts.find({"_id": {"$in": post_ids}})
    posts_map = {}
    async for p in posts_cursor:
        posts_map[p["_id"]] = p

    # return in bookmark order
    items = []
    for pid in post_ids:
        p = posts_map.get(pid)
        if not p:
            continue
        items.append({
            "id": str(p["_id"]),
            "topic_id": str(p["topic_id"]),
            "created_by": str(p["created_by"]),
            "body": p["body"],
            "created_at": p["created_at"],
            "updated_at": p.get("updated_at"),
            "upvote_count": p.get("upvote_count", 0),
            "comment_count": p.get("comment_count", 0),
        })
    return items
