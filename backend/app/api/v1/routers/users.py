from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.services.user_service import get_feed
from app.schemas.feed import FeedOut

router = APIRouter(prefix="/me", tags=["me"])

@router.get("/feed", response_model=FeedOut)
async def feed(
    user=Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    return await get_feed(user, limit=limit, skip=skip)
