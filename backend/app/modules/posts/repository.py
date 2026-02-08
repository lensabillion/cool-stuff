from app.core.database import get_app_db


async def get_topic(topic_id):
    return await get_app_db().topics.find_one({"_id": topic_id})


async def create_post(post_doc: dict):
    return await get_app_db().posts.insert_one(post_doc)


async def increment_topic_post_count(topic_id, delta: int):
    await get_app_db().topics.update_one({"_id": topic_id}, {"$inc": {"post_count": delta}})


async def list_posts(topic_id, skip: int, limit: int):
    cursor = get_app_db().posts.find({"topic_id": topic_id}).sort("created_at", -1).skip(skip).limit(limit)
    return [p async for p in cursor]


async def get_post(post_id):
    return await get_app_db().posts.find_one({"_id": post_id})


async def update_post(post_id, updates: dict):
    await get_app_db().posts.update_one({"_id": post_id}, {"$set": updates})


async def delete_post(post_id):
    await get_app_db().posts.delete_one({"_id": post_id})


async def cascade_delete_post_refs(post_id):
    await get_app_db().comments.delete_many({"post_id": post_id})
    await get_app_db().upvotes.delete_many({"post_id": post_id})
    await get_app_db().bookmarks.delete_many({"post_id": post_id})
