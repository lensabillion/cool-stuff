from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.common.mongo import now_utc, to_object_id
from app.modules.auth.schemas import CurrentUser
from app.modules.interactions import repository


async def upvote(post_id: str, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    if not await repository.get_post(post_oid):
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        await repository.create_upvote({"user_id": to_object_id(current_user.id), "post_id": post_oid, "created_at": now_utc()})
    except DuplicateKeyError:
        return {"upvoted": True}
    await repository.inc_post_counter(post_oid, "upvote_count", 1)
    return {"upvoted": True}


async def remove_upvote(post_id: str, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    res = await repository.delete_upvote(to_object_id(current_user.id), post_oid)
    if res.deleted_count:
        await repository.inc_post_counter(post_oid, "upvote_count", -1)
    return {"upvoted": False}


async def bookmark(post_id: str, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    if not await repository.get_post(post_oid):
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        await repository.create_bookmark(
            {"user_id": to_object_id(current_user.id), "post_id": post_oid, "created_at": now_utc()}
        )
    except DuplicateKeyError:
        return {"bookmarked": True}
    await repository.inc_post_counter(post_oid, "bookmark_count", 1)
    return {"bookmarked": True}


async def unbookmark(post_id: str, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    res = await repository.delete_bookmark(to_object_id(current_user.id), post_oid)
    if res.deleted_count:
        await repository.inc_post_counter(post_oid, "bookmark_count", -1)
    return {"bookmarked": False}
