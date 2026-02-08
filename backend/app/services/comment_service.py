from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import app_db

async def add_comment(post_id: str, body: str, current_user: dict) -> dict:
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")

    now = datetime.now(timezone.utc)
    doc = {
        "post_id": ObjectId(post_id),
        "created_by": ObjectId(current_user["id"]),
        "body": body,
        "created_at": now,
        "updated_at": None,
    }
    res = await app_db.comments.insert_one(doc)

    # increment comment counter on the post
    await app_db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$inc": {"comment_count": 1}}
    )

    return {
        "id": str(res.inserted_id),
        "post_id": post_id,
        "created_by": current_user["id"],
        "body": body,
        "created_at": now,
        "updated_at": None,
    }

async def list_comments(post_id: str, limit: int = 50, skip: int = 0) -> list[dict]:
    cursor = (
        app_db.comments.find({"post_id": ObjectId(post_id)})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )

    items = []
    async for c in cursor:
        items.append({
            "id": str(c["_id"]),
            "post_id": str(c["post_id"]),
            "created_by": str(c["created_by"]),
            "body": c["body"],
            "created_at": c["created_at"],
            "updated_at": c.get("updated_at"),
        })
    return items

async def update_comment(comment_id: str, body: str, current_user: dict) -> dict:
    comment = await app_db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise ValueError("Comment not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(comment["created_by"]) == current_user["id"]
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to edit this comment")

    now = datetime.now(timezone.utc)
    await app_db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"body": body, "updated_at": now}}
    )

    return {
        "id": comment_id,
        "post_id": str(comment["post_id"]),
        "created_by": str(comment["created_by"]),
        "body": body,
        "created_at": comment["created_at"],
        "updated_at": now,
    }

async def delete_comment(comment_id: str, current_user: dict) -> None:
    comment = await app_db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise ValueError("Comment not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(comment["created_by"]) == current_user["id"]
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to delete this comment")

    res = await app_db.comments.delete_one({"_id": ObjectId(comment_id)})
    if res.deleted_count == 1:
        await app_db.posts.update_one(
            {"_id": comment["post_id"]},
            {"$inc": {"comment_count": -1}}
        )
from datetime import datetime, timezone
from bson import ObjectId
from app.core.database import app_db

async def add_comment(post_id: str, body: str, current_user: dict) -> dict:
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")

    now = datetime.now(timezone.utc)
    doc = {
        "post_id": ObjectId(post_id),
        "created_by": ObjectId(current_user["id"]),
        "body": body,
        "created_at": now,
        "updated_at": None,
    }
    res = await app_db.comments.insert_one(doc)

    # increment comment counter on the post
    await app_db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$inc": {"comment_count": 1}}
    )

    return {
        "id": str(res.inserted_id),
        "post_id": post_id,
        "created_by": current_user["id"],
        "body": body,
        "created_at": now,
        "updated_at": None,
    }

async def list_comments(post_id: str, limit: int = 50, skip: int = 0) -> list[dict]:
    post = await app_db.posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise ValueError("Post not found")
    cursor = (
        app_db.comments.find({"post_id": ObjectId(post_id)})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )

    items = []
    async for c in cursor:
        items.append({
            "id": str(c["_id"]),
            "post_id": str(c["post_id"]),
            "created_by": str(c["created_by"]),
            "body": c["body"],
            "created_at": c["created_at"],
            "updated_at": c.get("updated_at"),
        })
    return items

async def update_comment(comment_id: str, body: str, current_user: dict) -> dict:
    comment = await app_db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise ValueError("Comment not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(comment["created_by"]) == current_user["id"]
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to edit this comment")

    now = datetime.now(timezone.utc)
    await app_db.comments.update_one(
        {"_id": ObjectId(comment_id)},
        {"$set": {"body": body, "updated_at": now}}
    )

    return {
        "id": comment_id,
        "post_id": str(comment["post_id"]),
        "created_by": str(comment["created_by"]),
        "body": body,
        "created_at": comment["created_at"],
        "updated_at": now,
    }

async def delete_comment(comment_id: str, current_user: dict) -> None:
    comment = await app_db.comments.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        raise ValueError("Comment not found")

    is_admin = current_user.get("role") == "admin"
    is_owner = str(comment["created_by"]) == current_user["id"]
    if not (is_admin or is_owner):
        raise PermissionError("Not allowed to delete this comment")

    res = await app_db.comments.delete_one({"_id": ObjectId(comment_id)})
    if res.deleted_count == 1:
        await app_db.posts.update_one(
            {"_id": comment["post_id"]},
            {"$inc": {"comment_count": -1}}
        )
