from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException
from app.core.database import app_db

async def create_topic(name: str, description: str | None, current_user: dict) -> dict:
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
        query = {"name": {"$regex": q, "$options": "i"}}

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

async def delete_topic(topic_id: str, current_user: dict) -> None:
    topic = await app_db.topics.find_one({"_id": ObjectId(topic_id)})
    if not topic:
        raise ValueError("Topic not found")

    is_admin = current_user.get("role") == "admin"
    is_creator = str(topic["created_by"]) == current_user["id"]

    if not (is_admin or is_creator):
        raise PermissionError("Not allowed to delete this topic")

    # If not admin, enforce "no other subscribers"
    if not is_admin:
        # count subscriptions excluding the creator
        others = await app_db.subscriptions.count_documents({
            "topic_id": ObjectId(topic_id),
            "user_id": {"$ne": ObjectId(current_user["id"])}
        })
        if others > 1:
            raise ValueError("Cannot delete topic: other subscribers exist")

    # delete topic + related data
    await app_db.topics.delete_one({"_id": ObjectId(topic_id)})
    await app_db.subscriptions.delete_many({"topic_id": ObjectId(topic_id)})

    # (Later, when posts exist, you’ll also delete posts/comments/upvotes/bookmarks for that topic.)
