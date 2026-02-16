from datetime import datetime, timezone
from bson import ObjectId

from app.core.database import app_db, auth_db
from app.core.cache import cache_delete_prefix


def _normalize_body(body: str) -> str:
    return body.strip()


async def create_post(topic_id: str, body: str, current_user: dict) -> dict:
    body = _normalize_body(body)
    if not body:
        raise ValueError("Body must not be empty")

    topic_oid = ObjectId(topic_id)

    # ensure topic exists
    topic = await app_db.topics.find_one({"_id": topic_oid})
    if not topic:
        raise ValueError("Topic not found")

    # Non-admin must be subscribed to post in topic
    if current_user.get("role") != "admin":
        sub = await app_db.subscriptions.find_one({
            "topic_id": topic_oid,
            "user_id": ObjectId(current_user["id"]),
        })
        if not sub:
            raise PermissionError("Must be subscribed to post in this topic")

    now = datetime.now(timezone.utc)

    doc = {
        "topic_id": topic_oid,
        "created_by": ObjectId(current_user["id"]),
        "body": body,
        "created_at": now,
        "updated_at": None,
        "upvote_count": 0,
        "comment_count": 0,
    }
    res = await app_db.posts.insert_one(doc)

    # update topic post_count
    await app_db.topics.update_one(
        {"_id": topic_oid},
        {"$inc": {"post_count": 1}}
    )

    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("me:feed")

    return {
        "id": str(res.inserted_id),
        "topic_id": topic_id,
        "created_by": current_user["id"],
        "created_by_username": current_user.get("username"),  # useful for UI
        "body": body,
        "created_at": now,
        "updated_at": None,
        "upvote_count": 0,
        "comment_count": 0,
    }


async def list_posts_by_topic(topic_id: str, limit: int = 20, skip: int = 0) -> list[dict]:
    topic_oid = ObjectId(topic_id)

    cursor = (
        app_db.posts.find({"topic_id": topic_oid})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    posts: list[dict] = []
    author_oids: list[ObjectId] = []

    async for p in cursor:
        author_oids.append(p["created_by"])
        posts.append({
            "id": str(p["_id"]),
            "topic_id": str(p["topic_id"]),
            "created_by": str(p["created_by"]),
            "created_by_username": None,  # filled below
            "body": p["body"],
            "created_at": p["created_at"],
            "updated_at": p.get("updated_at"),
            "upvote_count": p.get("upvote_count", 0),
            "comment_count": p.get("comment_count", 0),
        })

    # Attach usernames in one query (no N+1)
    if author_oids:
        unique_author_oids = list({oid for oid in author_oids})
        user_cursor = auth_db.users.find(
            {"_id": {"$in": unique_author_oids}},
            {"username": 1},
        )

        id_to_username: dict[str, str] = {}
        async for u in user_cursor:
            id_to_username[str(u["_id"])] = u.get("username", "")

        for post in posts:
            post["created_by_username"] = id_to_username.get(post["created_by"])

    return posts


async def update_post(post_id: str, body: str, current_user: dict) -> dict:
    body = _normalize_body(body)
    if not body:
        raise ValueError("Body must not be empty")

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

    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("me:feed")

    return {
        "id": post_id,
        "topic_id": str(post["topic_id"]),
        "created_by": str(post["created_by"]),
        "created_by_username": current_user.get("username"),  # if owner/admin; fine for UI
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

    post_oid = ObjectId(post_id)

    # delete related data
    await app_db.comments.delete_many({"post_id": post_oid})
    await app_db.upvotes.delete_many({"post_id": post_oid})
    await app_db.bookmarks.delete_many({"post_id": post_oid})

    await app_db.posts.delete_one({"_id": post_oid})

    # update topic post_count
    await app_db.topics.update_one(
        {"_id": post["topic_id"]},
        {"$inc": {"post_count": -1}}
    )

    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("posts:comments")
    await cache_delete_prefix("me:feed")
