# app/services/user_service.py
# No admin special-casing: everyone gets feed based ONLY on their subscriptions.

from bson import ObjectId
from bson.errors import InvalidId

from app.core.database import app_db, auth_db


def _to_oid(value: str, name: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise ValueError(f"Invalid {name}")


async def get_my_upvotes(current_user: dict, limit: int = 50, skip: int = 0) -> list[dict]:
    user_oid = ObjectId(current_user["id"])

    # 1) fetch upvotes by this user (most recent first)
    cursor = (
        app_db.upvotes.find({"user_id": user_oid}, {"post_id": 1, "created_at": 1})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    post_ids: list[ObjectId] = []
    upvoted_at_map: dict[str, datetime] = {}

    async for u in cursor:
        pid = u["post_id"]
        post_ids.append(pid)
        upvoted_at_map[str(pid)] = u.get("created_at")

    if not post_ids:
        return []

    # 2) fetch posts in one query
    posts_cursor = app_db.posts.find({"_id": {"$in": post_ids}})

    posts: list[dict] = []
    author_oids: list[ObjectId] = []

    async for p in posts_cursor:
        author_oids.append(p["created_by"])
        posts.append({
            "id": str(p["_id"]),
            "topic_id": str(p["topic_id"]),
            "created_by": str(p["created_by"]),
            "created_by_username": None,  # fill below
            "body": p["body"],
            "created_at": p["created_at"],
            "updated_at": p.get("updated_at"),
            "upvote_count": p.get("upvote_count", 0),
            "comment_count": p.get("comment_count", 0),
            "upvoted_at": upvoted_at_map.get(str(p["_id"])),
        })

    # 3) attach usernames in one query
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

    # 4) keep same order as upvotes
    order = {str(pid): i for i, pid in enumerate(post_ids)}
    posts.sort(key=lambda x: order.get(x["id"], 10**9))

    return posts
async def _get_subscription_topic_ids(current_user: dict) -> list[ObjectId]:
    """
    Return topic ObjectIds this user is subscribed to.
    Robust to legacy data where subscriptions.user_id could be ObjectId or string.
    """
    user_str = current_user["id"]
    user_oid = _to_oid(user_str, "user_id")

    topic_ids: list[ObjectId] = []
    cursor = app_db.subscriptions.find(
        {"$or": [{"user_id": user_oid}, {"user_id": user_str}]},
        {"topic_id": 1},
    )

    async for s in cursor:
        tid = s.get("topic_id")
        if tid:
            topic_ids.append(tid)

    # de-duplicate while preserving order
    seen = set()
    unique: list[ObjectId] = []
    for tid in topic_ids:
        if tid not in seen:
            seen.add(tid)
            unique.append(tid)

    return unique


async def get_my_subscriptions(current_user: dict, limit: int = 50, skip: int = 0) -> list[dict]:
    """
    GET /me/subscriptions
    Returns TopicOut[] for topics the current user is subscribed to.
    """
    topic_ids = await _get_subscription_topic_ids(current_user)

    # Apply pagination based on subscription order
    paged_ids = topic_ids[skip : skip + limit]
    if not paged_ids:
        return []

    topics_cursor = app_db.topics.find({"_id": {"$in": paged_ids}})

    topics: list[dict] = []
    async for t in topics_cursor:
        topics.append({
            "id": str(t["_id"]),
            "name": t["name"],
            "description": t.get("description"),
            "created_by": str(t["created_by"]),
            "created_at": t["created_at"],
            "subscriber_count": t.get("subscriber_count", 0),
            "post_count": t.get("post_count", 0),
        })

    # Keep the same order as subscriptions
    order = {str(tid): i for i, tid in enumerate(paged_ids)}
    topics.sort(key=lambda x: order.get(x["id"], 10**9))

    return topics


async def get_feed(current_user: dict, limit: int = 20, skip: int = 0) -> dict:
    """
    GET /me/feed
    Feed is ALWAYS posts from subscribed topics only.
    """
    topic_ids = await _get_subscription_topic_ids(current_user)
    subscription_count = len(topic_ids)

    if subscription_count == 0:
        return {"items": [], "subscription_count": 0, "reason_empty": "no_subscriptions"}

    query = {"topic_id": {"$in": topic_ids}}

    cursor = (
        app_db.posts.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    items: list[dict] = []
    author_oids: list[ObjectId] = []

    async for p in cursor:
        author_oids.append(p["created_by"])
        items.append({
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

    if len(items) == 0:
        return {"items": [], "subscription_count": subscription_count, "reason_empty": "no_posts"}

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

    return {"items": items, "subscription_count": subscription_count, "reason_empty": None}
