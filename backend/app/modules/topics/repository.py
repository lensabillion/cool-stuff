from typing import Any, Optional

from app.core.database import get_app_db


async def create_topic(doc: dict):
    return await get_app_db().topics.insert_one(doc)


async def list_topics(query: dict[str, Any], skip: int, limit: int):
    cursor = get_app_db().topics.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return [item async for item in cursor]


async def get_topic(topic_id):
    return await get_app_db().topics.find_one({"_id": topic_id})


async def create_subscription(doc: dict):
    return await get_app_db().subscriptions.insert_one(doc)


async def delete_subscription(user_id, topic_id):
    return await get_app_db().subscriptions.delete_one({"user_id": user_id, "topic_id": topic_id})


async def inc_topic_subscriber_count(topic_id, delta: int):
    await get_app_db().topics.update_one({"_id": topic_id}, {"$inc": {"subscriber_count": delta}})


async def other_subscriber_count(topic_id, user_id) -> int:
    return await get_app_db().subscriptions.count_documents({"topic_id": topic_id, "user_id": {"$ne": user_id}})


async def post_ids_by_topic(topic_id):
    return [p["_id"] async for p in get_app_db().posts.find({"topic_id": topic_id}, {"_id": 1})]


async def cascade_delete_posts(post_ids):
    if post_ids:
        await get_app_db().comments.delete_many({"post_id": {"$in": post_ids}})
        await get_app_db().upvotes.delete_many({"post_id": {"$in": post_ids}})
        await get_app_db().bookmarks.delete_many({"post_id": {"$in": post_ids}})


async def delete_posts_by_topic(topic_id):
    await get_app_db().posts.delete_many({"topic_id": topic_id})


async def delete_subscriptions_by_topic(topic_id):
    await get_app_db().subscriptions.delete_many({"topic_id": topic_id})


async def delete_topic(topic_id):
    await get_app_db().topics.delete_one({"_id": topic_id})
