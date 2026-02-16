import re
from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import app_db, auth_db
from app.core.cache import cache_delete_prefix


def _normalize_name(name: str) -> str:
    name = name.strip()
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

    # auto-subscribe creator
    await app_db.subscriptions.insert_one({
        "topic_id": topic_id,
        "user_id": created_by_oid,
        "created_at": now,
    })

    # invalidate caches (topics list + feed depends on subscriptions)
    await cache_delete_prefix("topics:list")
    await cache_delete_prefix("me:feed")

    return {
        "id": str(topic_id),
        "name": name,
        "description": description,
        "created_by": current_user["id"],
        "created_by_username": current_user.get("username"),
        "created_at": now,
        "subscriber_count": 1,
        "post_count": 0,
    }


async def list_topics(q: str | None, limit: int = 20, skip: int = 0) -> list[dict]:
    query = {}
    if q:
        safe = re.escape(q.strip())
        query = {"name": {"$regex": safe, "$options": "i"}}

    cursor = (
        app_db.topics.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    topics: list[dict] = []
    creator_oids: list[ObjectId] = []

    async for t in cursor:
        creator_oids.append(t["created_by"])
        topics.append({
            "id": str(t["_id"]),
            "name": t["name"],
            "description": t.get("description"),
            "created_by": str(t["created_by"]),
            "created_by_username": None,  # filled below
            "created_at": t["created_at"],
            "subscriber_count": t.get("subscriber_count", 0),
            "post_count": t.get("post_count", 0),
        })

    # attach creator usernames in one query
    if creator_oids:
        unique_creator_oids = list({oid for oid in creator_oids})
        user_cursor = auth_db.users.find(
            {"_id": {"$in": unique_creator_oids}},
            {"username": 1},
        )

        id_to_username: dict[str, str] = {}
        async for u in user_cursor:
            id_to_username[str(u["_id"])] = u.get("username", "")

        for topic in topics:
            topic["created_by_username"] = id_to_username.get(topic["created_by"])

    return topics


async def subscribe(topic_id: str, current_user: dict) -> None:
    topic_oid = ObjectId(topic_id)

    # ensure topic exists
    topic = await app_db.topics.find_one({"_id": topic_oid})
    if not topic:
        raise ValueError("Topic not found")

    user_oid = ObjectId(current_user["id"])

    # prevent duplicate subscribe
    existing = await app_db.subscriptions.find_one({
        "topic_id": topic_oid,
        "user_id": user_oid,
    })
    if existing:
        return  # idempotent

    await app_db.subscriptions.insert_one({
        "topic_id": topic_oid,
        "user_id": user_oid,
        "created_at": datetime.now(timezone.utc),
    })

    # update counter
    await app_db.topics.update_one(
        {"_id": topic_oid},
        {"$inc": {"subscriber_count": 1}}
    )

    # invalidate caches
    await cache_delete_prefix("topics:list")
    await cache_delete_prefix("me:feed")


async def unsubscribe(topic_id: str, current_user: dict) -> None:
    topic_oid = ObjectId(topic_id)
    user_oid = ObjectId(current_user["id"])

    res = await app_db.subscriptions.delete_one({
        "topic_id": topic_oid,
        "user_id": user_oid,
    })

    if res.deleted_count == 1:
        await app_db.topics.update_one(
            {"_id": topic_oid},
            {"$inc": {"subscriber_count": -1}}
        )

    # invalidate caches
    await cache_delete_prefix("topics:list")
    await cache_delete_prefix("me:feed")


async def delete_topic(topic_id: str, current_user: dict) -> None:
    topic_oid = ObjectId(topic_id)

    topic = await app_db.topics.find_one({"_id": topic_oid})
    if not topic:
        raise ValueError("Topic not found")

    is_admin = current_user.get("role") == "admin"
    is_creator = str(topic["created_by"]) == current_user["id"]

    # only admin or creator can delete
    if not (is_admin or is_creator):
        raise PermissionError("Not allowed to delete this topic")

    # --- CASCADE DELETE ---

    # collect post ids under this topic
    post_ids: list[ObjectId] = []
    cursor = app_db.posts.find({"topic_id": topic_oid}, {"_id": 1})
    async for p in cursor:
        post_ids.append(p["_id"])

    # delete post-related data
    if post_ids:
        await app_db.comments.delete_many({"post_id": {"$in": post_ids}})
        await app_db.upvotes.delete_many({"post_id": {"$in": post_ids}})
        await app_db.bookmarks.delete_many({"post_id": {"$in": post_ids}})
        await app_db.posts.delete_many({"_id": {"$in": post_ids}})

    # delete subscriptions for this topic
    await app_db.subscriptions.delete_many({"topic_id": topic_oid})

    # delete the topic itself
    await app_db.topics.delete_one({"_id": topic_oid})

    # invalidate caches
    await cache_delete_prefix("topics:list")
    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("posts:comments")
    await cache_delete_prefix("me:feed")
