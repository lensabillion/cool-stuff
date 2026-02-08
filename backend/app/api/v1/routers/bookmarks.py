from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.dependencies import get_current_user
from app.schemas.post import PostOut
from app.services.bookmark_service import bookmark_post, unbookmark_post, list_my_bookmarks

router = APIRouter(tags=["bookmarks"])

@router.post("/posts/{post_id}/bookmark", status_code=204)
async def bookmark(post_id: str, user=Depends(get_current_user)):
    try:
        await bookmark_post(post_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/posts/{post_id}/bookmark", status_code=204)
async def unbookmark(post_id: str, user=Depends(get_current_user)):
    await unbookmark_post(post_id, user)

@router.get("/me/bookmarks", response_model=list[PostOut])
async def my_bookmarks(
    user=Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    return await list_my_bookmarks(user, limit=limit, skip=skip)
