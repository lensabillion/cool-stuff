from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.common.utils import PostType
from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUser
from app.modules.posts.schemas import PostUpdateRequest
from app.modules.posts import service

router = APIRouter(tags=["posts"])


@router.post("/api/v1/topics/{topic_id}/posts")
async def create_post_route(
    topic_id: str,
    type: PostType = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(default=None),
    url: Optional[str] = Form(default=None),
    pdf: Optional[UploadFile] = File(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    return await service.create_post(topic_id, type, title, description, url, pdf, current_user)


@router.get("/api/v1/topics/{topic_id}/posts")
async def list_posts_route(topic_id: str, skip: int = 0, limit: int = 20):
    return await service.list_posts(topic_id, skip, limit)


@router.patch("/api/v1/posts/{post_id}")
async def edit_post_route(post_id: str, payload: PostUpdateRequest, current_user: CurrentUser = Depends(get_current_user)):
    return await service.edit_post(post_id, payload, current_user)


@router.delete("/api/v1/posts/{post_id}")
async def delete_post_route(post_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.delete_post(post_id, current_user)
