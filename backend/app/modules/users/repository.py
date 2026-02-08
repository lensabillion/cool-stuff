from app.core.database import get_app_db


async def bookmarked_post_ids(user_id, skip: int, limit: int):
    return [
        b["post_id"]
        async for b in get_app_db().bookmarks.find({"user_id": user_id}, {"post_id": 1}).skip(skip).limit(limit)
    ]


async def posts_by_ids(post_ids):
    cursor = get_app_db().posts.find({"_id": {"$in": post_ids}}).sort("created_at", -1)
    return [p async for p in cursor]


async def subscription_topic_ids(user_id):
    return [s["topic_id"] async for s in get_app_db().subscriptions.find({"user_id": user_id}, {"topic_id": 1})]


async def posts_by_topic_ids(topic_ids, skip: int, limit: int):
    cursor = get_app_db().posts.find({"topic_id": {"$in": topic_ids}}).sort("created_at", -1).skip(skip).limit(limit)
    return [p async for p in cursor]
