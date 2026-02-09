from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_user
from app.schemas.topic import TopicCreate, TopicOut
from app.services.topic_service import create_topic, list_topics, subscribe, unsubscribe, delete_topic

from app.core.rate_limit import rate_limit_user
from app.core.rate_limit_rules import RULES

from app.core.cache import make_key, cache_get, cache_set
router = APIRouter(prefix="/topics", tags=["topics"])

@router.post("", response_model=TopicOut, status_code=201)
async def create(payload: TopicCreate, user=Depends(get_current_user)):
   
    limit, window = RULES["topics:create_user"]
    await rate_limit_user(user, action="topics:create", limit=limit, window_seconds=window)

    try:
        return await create_topic(payload.name, payload.description, user)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("", response_model=list[TopicOut])
async def list_(
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    q_norm = q.strip().lower() if q else None
    key = make_key("topics:list", f"q={q_norm}", f"limit={limit}", f"skip={skip}")

    cached = await cache_get(key)
    if cached is not None:
        return cached

    result = await list_topics(q=q_norm, limit=limit, skip=skip)
    await cache_set(key, result, ttl_seconds=30)  # 30s TTL
    return result
    

@router.post("/{topic_id}/subscribe", status_code=204)
async def sub(topic_id: str, user=Depends(get_current_user)):
    
    limit, window = RULES["topics:subscribe_user"]
    await rate_limit_user(user, action="topics:subscribe", limit=limit, window_seconds=window)

    try:
        await subscribe(topic_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{topic_id}/unsubscribe", status_code=204)
async def unsub(topic_id: str, user=Depends(get_current_user)):
   
    limit, window = RULES["topics:unsubscribe_user"]
    await rate_limit_user(user, action="topics:unsubscribe", limit=limit, window_seconds=window)

    await unsubscribe(topic_id, user)
@router.delete("/{topic_id}", status_code=204)
async def delete_(topic_id: str, user=Depends(get_current_user)):

    limit, window = RULES["topics:delete_user"]
    await rate_limit_user(user, action="topics:delete", limit=limit, window_seconds=window)

    try:
        await delete_topic(topic_id, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        # not found or constraint violation
        msg = str(e)
        if msg == "Topic not found":
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)