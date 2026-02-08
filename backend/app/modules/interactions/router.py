from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUser
from app.modules.interactions import service

router = APIRouter(tags=["interactions"])


@router.post("/api/v1/posts/{post_id}/upvote")
async def upvote_route(post_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.upvote(post_id, current_user)


@router.delete("/api/v1/posts/{post_id}/upvote")
async def remove_upvote_route(post_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.remove_upvote(post_id, current_user)


@router.post("/api/v1/posts/{post_id}/bookmark")
async def bookmark_route(post_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.bookmark(post_id, current_user)


@router.delete("/api/v1/posts/{post_id}/bookmark")
async def unbookmark_route(post_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.unbookmark(post_id, current_user)
