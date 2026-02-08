from fastapi import APIRouter
from app.api.v1.routers import health, auth, topics, posts, users, comments, upvotes, bookmarks

router = APIRouter()  # no prefix!

router.include_router(health.router)
router.include_router(auth.router)
router.include_router(topics.router)
router.include_router(posts.router)
router.include_router(users.router)
router.include_router(comments.router)
router.include_router(upvotes.router)
router.include_router(bookmarks.router)