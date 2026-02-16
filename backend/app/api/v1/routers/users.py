from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.services.user_service import get_feed,get_my_subscriptions
from app.schemas.feed import FeedOut
from app.schemas.topic import TopicOut
from app.schemas.me import UpvotedPostItem
from app.services.user_service import get_my_upvotes

router = APIRouter(prefix="/me", tags=["me"])

@router.get("/upvotes", response_model=list[UpvotedPostItem])
async def my_upvotes(
    user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    return await get_my_upvotes(user, limit=limit, skip=skip)
@router.get("/upvotes", response_model=list[UpvotedPostItem])
async def my_upvotes(
    user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    return await get_my_upvotes(user, limit=limit, skip=skip)
@router.get("/feed", response_model=FeedOut)
async def feed(
    user=Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    return await get_feed(user, limit=limit, skip=skip)
@router.get("/subscriptions", response_model=list[TopicOut])
async def my_subscriptions(
    user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    return await get_my_subscriptions(user, limit=limit, skip=skip)
