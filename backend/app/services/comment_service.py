from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

from app.core.database import app_db, auth_db
from app.core.cache import cache_delete_prefix


def to_oid(value: str, *, name: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {name}")


def normalize_body(body: str) -> str:
    body = body.strip()
    if not body:
        raise HTTPException(status_code=422, detail="Body must not be empty")
    return body


async def add_comment(post_id: str, body: str, current_user: dict) -> dict:
    post_oid = to_oid(post_id, name="post_id")
    user_oid = to_oid(current_user["id"], name="user_id")
    body = normalize_body(body)

    post = await app_db.posts.find_one({"_id": post_oid})
    if not post:
        raise ValueError("Post not found")

    now = datetime.now(timezone.utc)
    doc = {
        "post_id": post_oid,
        "created_by": user_oid,
        "body": body,
        "created_at": now,
        "updated_at": None,
    }
    res = await app_db.comments.insert_one(doc)

    # increment comment counter on the post
    await app_db.posts.update_one({"_id": post_oid}, {"$inc": {"comment_count": 1}})

    # invalidate caches
    await cache_delete_prefix("posts:comments")
    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("me:feed")

    return {
        "id": str(res.inserted_id),
        "post_id": post_id,
        "created_by": current_user["id"],
        "created_by_username": current_user.get("username"),  # ✅ for UI
        "body": body,
        "created_at": now,
        "updated_at": None,
    }


async def list_comments(post_id: str, limit: int = 50, skip: int = 0) -> list[dict]:
    post_oid = to_oid(post_id, name="post_id")

    # Better UX: if post doesn't exist, return 404-ish error
    post = await app_db.posts.find_one({"_id": post_oid})
    if not post:
        raise ValueError("Post not found")

    cursor = (
        app_db.comments.find({"post_id": post_oid})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )

    items: list[dict] = []
    author_oids: list[ObjectId] = []

    async for c in cursor:
        author_oids.append(c["created_by"])
        items.append({
            "id": str(c["_id"]),
            "post_id": str(c["post_id"]),
            "created_by": str(c["created_by"]),
            "created_by_username": None,  # filled below
            "body": c["body"],
            "created_at": c["created_at"],
            "updated_at": c.get("updated_at"),
        })

    # Attach usernames in one query
    if author_oids:
        unique_author_oids = list({oid for oid in author_oids})
        user_cursor = auth_db.users.find(
            {"_id": {"$in": unique_author_oids}},
            {"username": 1},
        )

        id_to_username: dict[str, str] = {}
        async for u in user_cursor:
            id_to_username[str(u["_id"])] = u.get("username", "")

        for it in items:
            it["created_by_username"] = id_to_username.get(it["created_by"])

    return items


async def update_comment(comment_id: str, body: str, current_user: dict) -> dict:
    comment_oid = to_oid(comment_id, name="comment_id")
    user_id = current_user["id"]
    body = normalize_body(body)

    comment = await app_db.comments.find_one({"_id": comment_oid})
    if not comment:
        raise ValueError("Comment not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(comment["created_by"]) == user_id
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to edit this comment")

    now = datetime.now(timezone.utc)
    await app_db.comments.update_one(
        {"_id": comment_oid},
        {"$set": {"body": body, "updated_at": now}},
    )

    await cache_delete_prefix("posts:comments")
    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("me:feed")

    # determine username for response (nice for UI)
    username = None
    if is_owner:
        username = current_user.get("username")
    else:
        # admin editing someone else's comment -> fetch username of original author (optional)
        u = await auth_db.users.find_one({"_id": comment["created_by"]}, {"username": 1})
        if u:
            username = u.get("username")

    return {
        "id": comment_id,
        "post_id": str(comment["post_id"]),
        "created_by": str(comment["created_by"]),
        "created_by_username": username,
        "body": body,
        "created_at": comment["created_at"],
        "updated_at": now,
    }


async def delete_comment(comment_id: str, current_user: dict) -> None:
    comment_oid = to_oid(comment_id, name="comment_id")
    user_id = current_user["id"]

    comment = await app_db.comments.find_one({"_id": comment_oid})
    if not comment:
        raise ValueError("Comment not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(comment["created_by"]) == user_id
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to delete this comment")

    res = await app_db.comments.delete_one({"_id": comment_oid})
    if res.deleted_count == 1:
        await app_db.posts.update_one(
            {"_id": comment["post_id"]},
            {"$inc": {"comment_count": -1}},
        )

    await cache_delete_prefix("posts:comments")
    await cache_delete_prefix("topics:posts")
    await cache_delete_prefix("me:feed")
