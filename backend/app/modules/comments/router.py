from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUser
from app.modules.comments import service
from app.modules.comments.schemas import CommentCreateRequest, CommentUpdateRequest

router = APIRouter(tags=["comments"])


@router.post("/api/v1/posts/{post_id}/comments")
async def create_comment_route(post_id: str, payload: CommentCreateRequest, current_user: CurrentUser = Depends(get_current_user)):
    return await service.create_comment(post_id, payload, current_user)


@router.get("/api/v1/posts/{post_id}/comments")
async def list_comments_route(post_id: str, skip: int = 0, limit: int = 30):
    return await service.list_comments(post_id, skip, limit)


@router.patch("/api/v1/comments/{comment_id}")
async def edit_comment_route(comment_id: str, payload: CommentUpdateRequest, current_user: CurrentUser = Depends(get_current_user)):
    return await service.edit_comment(comment_id, payload, current_user)


@router.delete("/api/v1/comments/{comment_id}")
async def delete_comment_route(comment_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.delete_comment(comment_id, current_user)
