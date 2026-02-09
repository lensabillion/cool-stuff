import re
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException
from app.core.database import app_db
from app.core.cache import cache_delete_prefix

def _normalize_name(name: str) -> str:
    name = name.strip()
    # extra safety: collapse multiple spaces
    name = re.sub(r"\s+", " ", name)
    return name
def _normalize_description(description: str | None) -> str | None:
    if description is None:
        return None
    d = description.strip()
    return d if d else None

async def create_topic(name: str, description: str | None, current_user: dict) -> dict:
    name = _normalize_name(name)
    description = _normalize_description(description)

    # enforce unique name
    existing = await app_db.topics.find_one({"name": name})
    if existing:
        raise ValueError("Topic name already exists")

    created_by_oid = ObjectId(current_user["id"])
    now = datetime.now(timezone.utc)

    doc = {
        "name": name,
        "description": description,
        "created_by": created_by_oid,
        "created_at": now,
        "subscriber_count": 1,
        "post_count": 0,
    }
    res = await app_db.topics.insert_one(doc)
    topic_id = res.inserted_id

    # 2) auto-subscribe creator
    await app_db.subscriptions.insert_one({
        "topic_id": topic_id,
        "user_id": created_by_oid,
        "created_at": now,
    })
    await cache_delete_prefix("topics:list")
    return {
        "id": str(res.inserted_id),
        "name": name,
        "description": description,
        "created_by": current_user["id"],
        "created_at": now,
        "subscriber_count": 1,
        "post_count": 0,
    }

async def list_topics(q: str | None, limit: int = 20, skip: int = 0) -> list[dict]:
    query = {}
    if q:
        # simple search by name (we can improve later with text index)
        safe = re.escape(q.strip())
        query = {"name": {"$regex": safe, "$options": "i"}}

    cursor = (
        app_db.topics.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    topics = []
    async for t in cursor:
        topics.append({
            "id": str(t["_id"]),
            "name": t["name"],
            "description": t.get("description"),
            "created_by": str(t["created_by"]),
            "created_at": t["created_at"],
            "subscriber_count": t.get("subscriber_count", 0),
            "post_count": t.get("post_count", 0),
        })
    return topics

async def subscribe(topic_id: str, current_user: dict) -> None:
    # ensure topic exists
    topic = await app_db.topics.find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise ValueError("Topic not found")

    # prevent duplicate subscribe
    existing = await app_db.subscriptions.find_one({
        "topic_id": ObjectId(topic_id),
        "user_id": ObjectId(current_user["id"]),
    })
    if existing:
        return  # idempotent

    await app_db.subscriptions.insert_one({
        "topic_id": ObjectId(topic_id),
        "user_id": ObjectId(current_user["id"]),
        "created_at": datetime.now(timezone.utc),
    })
    

    # update counter
    await app_db.topics.update_one(
        {"_id": ObjectId(topic_id)},
        {"$inc": {"subscriber_count": 1}}
    )
    await cache_delete_prefix("topics:list")
async def unsubscribe(topic_id: str, current_user: dict) -> None:
    res = await app_db.subscriptions.delete_one({
        "topic_id": ObjectId(topic_id),
        "user_id": ObjectId(current_user["id"]),
    })

    if res.deleted_count == 1:
        await app_db.topics.update_one(
            {"_id": ObjectId(topic_id)},
            {"$inc": {"subscriber_count": -1}}
        )
    await cache_delete_prefix("topics:list")

async def delete_topic(topic_id: str, current_user: dict) -> None:
    topic_oid = ObjectId(topic_id)

    topic = await app_db.topics.find_one({"_id": topic_oid})
    if not topic:
        raise ValueError("Topic not found")

    is_admin = current_user.get("role") == "admin"
    is_creator = str(topic["created_by"]) == current_user["id"]

    # ✅ Only admin or creator can delete
    if not (is_admin or is_creator):
        raise PermissionError("Not allowed to delete this topic")

    # --- CASCADE DELETE ---

    # 1) collect post ids under this topic
    post_ids: list[ObjectId] = []
    cursor = app_db.posts.find({"topic_id": topic_oid}, {"_id": 1})
    async for p in cursor:
        post_ids.append(p["_id"])

    # 2) delete all post-related data
    if post_ids:
        await app_db.comments.delete_many({"post_id": {"$in": post_ids}})
        await app_db.upvotes.delete_many({"post_id": {"$in": post_ids}})
        await app_db.bookmarks.delete_many({"post_id": {"$in": post_ids}})
        await app_db.posts.delete_many({"_id": {"$in": post_ids}})

    # 3) delete subscriptions for this topic
    await app_db.subscriptions.delete_many({"topic_id": topic_oid})

    # 4) delete the topic itself
    await app_db.topics.delete_one({"_id": topic_oid})

    # 5) invalidate caches
    await cache_delete_prefix("topics:list")
    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("posts:comments")
    await cache_delete_prefix("me:feed")