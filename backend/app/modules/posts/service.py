from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile

from app.common.mongo import now_utc, serialize_mongo, to_object_id
from app.common.pagination import normalize_pagination
from app.common.utils import PostType, Role
from app.modules.auth.schemas import CurrentUser
from app.modules.posts import repository, storage
from app.modules.posts.schemas import PostUpdateRequest


def can_manage(owner_id, user: CurrentUser) -> bool:
    return user.role == Role.admin or owner_id == to_object_id(user.id)


async def create_post(
    topic_id: str,
    type: PostType,
    title: str,
    description: Optional[str],
    url: Optional[str],
    pdf: Optional[UploadFile],
    current_user: CurrentUser,
):
    topic_oid = to_object_id(topic_id)
    if not await repository.get_topic(topic_oid):
        raise HTTPException(status_code=404, detail="Topic not found")

    post_doc = {
        "topic_id": topic_oid,
        "created_by": to_object_id(current_user.id),
        "type": type.value,
        "title": title,
        "description": description,
        "upvote_count": 0,
        "comment_count": 0,
        "bookmark_count": 0,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }

    if type == PostType.link:
        if not url:
            raise HTTPException(status_code=400, detail="url required for link posts")
        post_doc["url"] = url
    else:
        _, full_path = storage.save_pdf_upload(pdf)
        Path(full_path).write_bytes(await pdf.read())
        post_doc["pdf_path"] = full_path
        post_doc["pdf_filename"] = pdf.filename

    result = await repository.create_post(post_doc)
    await repository.increment_topic_post_count(topic_oid, 1)
    post_doc["_id"] = result.inserted_id
    return serialize_mongo(post_doc)


async def list_posts(topic_id: str, skip: int, limit: int):
    skip, limit = normalize_pagination(skip, limit)
    docs = await repository.list_posts(to_object_id(topic_id), skip, limit)
    return [serialize_mongo(d) for d in docs]


async def edit_post(post_id: str, payload: PostUpdateRequest, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    post = await repository.get_post(post_oid)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not can_manage(post["created_by"], current_user):
        raise HTTPException(status_code=403, detail="Forbidden")

    updates = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    if post["type"] == PostType.pdf.value and "url" in updates:
        raise HTTPException(status_code=400, detail="PDF posts do not have url")
    if not updates:
        raise HTTPException(status_code=400, detail="No changes submitted")

    updates["updated_at"] = now_utc()
    await repository.update_post(post_oid, updates)
    post.update(updates)
    return serialize_mongo(post)


async def delete_post(post_id: str, current_user: CurrentUser):
    post_oid = to_object_id(post_id)
    post = await repository.get_post(post_oid)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not can_manage(post["created_by"], current_user):
        raise HTTPException(status_code=403, detail="Forbidden")

    await repository.cascade_delete_post_refs(post_oid)
    await repository.delete_post(post_oid)
    await repository.increment_topic_post_count(post["topic_id"], -1)
    return {"deleted": True}
