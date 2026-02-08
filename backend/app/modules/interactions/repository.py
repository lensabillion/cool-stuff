from app.core.database import get_app_db


async def get_post(post_id):
    return await get_app_db().posts.find_one({"_id": post_id})


async def create_upvote(doc: dict):
    return await get_app_db().upvotes.insert_one(doc)


async def delete_upvote(user_id, post_id):
    return await get_app_db().upvotes.delete_one({"user_id": user_id, "post_id": post_id})


async def create_bookmark(doc: dict):
    return await get_app_db().bookmarks.insert_one(doc)


async def delete_bookmark(user_id, post_id):
    return await get_app_db().bookmarks.delete_one({"user_id": user_id, "post_id": post_id})


async def inc_post_counter(post_id, field: str, delta: int):
    await get_app_db().posts.update_one({"_id": post_id}, {"$inc": {field: delta}})
