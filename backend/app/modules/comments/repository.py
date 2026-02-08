from app.core.database import get_app_db


async def get_post(post_id):
    return await get_app_db().posts.find_one({"_id": post_id})


async def create_comment(doc: dict):
    return await get_app_db().comments.insert_one(doc)


async def increment_post_comment_count(post_id, delta: int):
    await get_app_db().posts.update_one({"_id": post_id}, {"$inc": {"comment_count": delta}})


async def list_comments(post_id, skip: int, limit: int):
    cursor = get_app_db().comments.find({"post_id": post_id}).sort("created_at", 1).skip(skip).limit(limit)
    return [c async for c in cursor]


async def get_comment(comment_id):
    return await get_app_db().comments.find_one({"_id": comment_id})


async def update_comment(comment_id, updates: dict):
    await get_app_db().comments.update_one({"_id": comment_id}, {"$set": updates})


async def delete_comment(comment_id):
    await get_app_db().comments.delete_one({"_id": comment_id})
