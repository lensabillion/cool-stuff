from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUser
from app.modules.users import service

router = APIRouter(prefix="/api/v1/me", tags=["users"])


@router.get("/bookmarks")
async def my_bookmarks_route(current_user: CurrentUser = Depends(get_current_user), skip: int = 0, limit: int = 20):
    return await service.my_bookmarks(current_user, skip, limit)


@router.get("/feed")
async def my_feed_route(current_user: CurrentUser = Depends(get_current_user), skip: int = 0, limit: int = 20):
    return await service.my_feed(current_user, skip, limit)
