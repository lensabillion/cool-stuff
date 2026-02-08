from fastapi import HTTPException

from app.common.mongo import now_utc, serialize_mongo, to_object_id
from app.common.pagination import normalize_pagination
from app.common.utils import Role
from app.modules.auth.schemas import CurrentUser
from app.modules.comments import repository
from app.modules.comments.schemas import CommentCreateRequest, CommentUpdateRequest


def can_manage(owner_id, current_user: CurrentUser) -> bool:
    return current_user.role == Role.admin or owner_id == to_object_id(current_user.id)


async def create_comment(post_id: str, payload: CommentCreateRequest, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    if not await repository.get_post(post_oid):
        raise HTTPException(status_code=404, detail="Post not found")

    comment = {
        "post_id": post_oid,
        "created_by": to_object_id(current_user.id),
        "body": payload.body,
        "created_at": now_utc(),
        "updated_at": None,
    }
    result = await repository.create_comment(comment)
    await repository.increment_post_comment_count(post_oid, 1)
    comment["_id"] = result.inserted_id
    return serialize_mongo(comment)


async def list_comments(post_id: str, skip: int, limit: int):
    skip, limit = normalize_pagination(skip, limit)
    docs = await repository.list_comments(to_object_id(post_id), skip, limit)
    return [serialize_mongo(d) for d in docs]


async def edit_comment(comment_id: str, payload: CommentUpdateRequest, current_user: CurrentUser):
    comment_oid = to_object_id(comment_id)
    comment = await repository.get_comment(comment_oid)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not can_manage(comment["created_by"], current_user):
        raise HTTPException(status_code=403, detail="Forbidden")

    updates = {"body": payload.body, "updated_at": now_utc(), "edited": True}
    await repository.update_comment(comment_oid, updates)
    comment.update(updates)
    return serialize_mongo(comment)


async def delete_comment(comment_id: str, current_user: CurrentUser):
    comment_oid = to_object_id(comment_id)
    comment = await repository.get_comment(comment_oid)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if not can_manage(comment["created_by"], current_user):
        raise HTTPException(status_code=403, detail="Forbidden")
    await repository.delete_comment(comment_oid)
    await repository.increment_post_comment_count(comment["post_id"], -1)
    return {"deleted": True}
