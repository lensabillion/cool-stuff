from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_user
from app.schemas.comment import CommentCreate, CommentUpdate, CommentOut
from app.services.comment_service import add_comment, list_comments, update_comment, delete_comment
from app.core.rate_limit import rate_limit_user
from app.core.rate_limit_rules import RULES
from app.core.cache import make_key, cache_get, cache_set

router = APIRouter(tags=["comments"])

@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
async def create(post_id: str, payload: CommentCreate, user=Depends(get_current_user)):
   
    limit, window = RULES["comments:create_user"]
    await rate_limit_user(user, action="comments:create", limit=limit, window_seconds=window)

    try:
        return await add_comment(post_id, payload.body, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
async def list_(
    post_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
):
    key = make_key("posts:comments",f"post={post_id}", f"limit={limit}", f"skip={skip}")
    cached = await cache_get(key)
    if cached is not None:
        return cached

    try:
        result = await list_comments(post_id, limit=limit, skip=skip)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await cache_set(key, result, ttl_seconds=20)
    return result
@router.put("/comments/{comment_id}", response_model=CommentOut)
async def edit(comment_id: str, payload: CommentUpdate, user=Depends(get_current_user)):
    
    limit, window = RULES["comments:update_user"]
    await rate_limit_user(user, action="comments:update", limit=limit, window_seconds=window)

    try:
        return await update_comment(comment_id, payload.body, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/comments/{comment_id}", status_code=204)
async def delete_(comment_id: str, user=Depends(get_current_user)):
    
    limit, window = RULES["comments:delete_user"]
    await rate_limit_user(user, action="comments:delete", limit=limit, window_seconds=window)

    try:
        await delete_comment(comment_id, user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
