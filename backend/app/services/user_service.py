from bson import ObjectId
from app.core.database import app_db

async def get_feed(current_user: dict, limit: int = 20, skip: int = 0) -> dict:
    # Admin: global feed
    if current_user.get("role") == "admin":
        query = {}
        subscription_count = 0  # not relevant for admin global feed
    else:
        topic_ids = []
        cursor = app_db.subscriptions.find({"user_id": ObjectId(current_user["id"])})
        async for s in cursor:
            topic_ids.append(s["topic_id"])

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

    items = []
    async for p in cursor:
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

    if len(items) == 0 and current_user.get("role") != "admin":
        return {"items": [], "subscription_count": subscription_count, "reason_empty": "no_posts"}

    return {"items": items, "subscription_count": subscription_count, "reason_empty": None}
