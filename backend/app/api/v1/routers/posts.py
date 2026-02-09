from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.rate_limit import rate_limit_user
from app.core.rate_limit_rules import RULES
from app.core.cache import make_key, cache_get, cache_set
from app.core.dependencies import get_current_user
from app.schemas.post import PostCreateText, PostUpdateText, PostOut
from app.services.post_service import (
    create_post,
    list_posts_by_topic,
    update_post,
    delete_post,
)

router = APIRouter(tags=["posts"])

@router.post("/topics/{topic_id}/posts", response_model=PostOut, status_code=201)
async def create(topic_id: str, payload: PostCreateText, user=Depends(get_current_user)):
    
    limit, window = RULES["posts:create_user"]
    await rate_limit_user(user, action="posts:create", limit=limit, window_seconds=window)

    try:
        return await create_post(topic_id, payload.body, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
@router.get("/topics/{topic_id}/posts", response_model=list[PostOut])
async def list_(
    topic_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
   
    key = make_key("topics:posts", f"topic={topic_id}", f"limit={limit}", f"skip={skip}")

    cached = await cache_get(key)
    if cached is not None:
        return cached

    result = await list_posts_by_topic(topic_id, limit=limit, skip=skip)
    await cache_set(key, result, ttl_seconds=20)  # 20s TTL (posts change more often)
    return result

@router.put("/posts/{post_id}", response_model=PostOut)
async def edit(post_id: str, payload: PostUpdateText, user=Depends(get_current_user)):
    
    limit, window = RULES["posts:update_user"]
    await rate_limit_user(user, action="posts:update", limit=limit, window_seconds=window)

    try:
        return await update_post(post_id, payload.body, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/posts/{post_id}", status_code=204)
async def delete_(post_id: str, user=Depends(get_current_user)):
    
    limit, window = RULES["posts:delete_user"]
    await rate_limit_user(user, action="posts:delete", limit=limit, window_seconds=window)

    try:
        await delete_post(post_id, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
