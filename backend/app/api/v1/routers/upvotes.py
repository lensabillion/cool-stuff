from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.services.upvote_service import upvote_post, remove_upvote
from app.core.rate_limit import rate_limit_user
from app.core.rate_limit_rules import RULES

router = APIRouter(tags=["upvotes"])

@router.post("/posts/{post_id}/upvote", status_code=204)
async def upvote(post_id: str, user=Depends(get_current_user)):
    limit, window = RULES["upvotes:toggle_user"]
    await rate_limit_user(user, action="upvotes:toggle", limit=limit, window_seconds=window)

    try:
        await upvote_post(post_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/posts/{post_id}/upvote", status_code=204)
async def unupvote(post_id: str, user=Depends(get_current_user)):
    limit, window = RULES["upvotes:toggle_user"]
    await rate_limit_user(user, action="upvotes:toggle", limit=limit, window_seconds=window)

    await remove_upvote(post_id, user)
