from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.modules.auth.schemas import CurrentUser
from app.modules.topics.schemas import TopicCreateRequest, TopicResponse
from app.modules.topics import service

router = APIRouter(prefix="/api/v1/topics", tags=["topics"])


@router.post("", response_model=TopicResponse)
async def create_topic_route(payload: TopicCreateRequest, current_user: CurrentUser = Depends(get_current_user)):
    return await service.create_topic(payload, current_user)


@router.get("")
async def list_topics_route(q: Optional[str] = Query(default=None), skip: int = 0, limit: int = 20):
    return await service.list_topics(q, skip, limit)


@router.post("/{topic_id}/subscribe")
async def subscribe_route(topic_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.subscribe(topic_id, current_user)


@router.delete("/{topic_id}/subscribe")
async def unsubscribe_route(topic_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.unsubscribe(topic_id, current_user)


@router.delete("/{topic_id}")
async def delete_topic_route(topic_id: str, current_user: CurrentUser = Depends(get_current_user)):
    return await service.delete_topic(topic_id, current_user)
