from fastapi import FastAPI

from app.core.database import close_db, connect_db
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.modules.auth.router import router as auth_router
from app.modules.comments.router import router as comments_router
from app.modules.interactions.router import router as interactions_router
from app.modules.posts.router import router as posts_router
from app.modules.topics.router import router as topics_router
from app.modules.users.router import router as users_router

setup_logging()

app = FastAPI(title="CoolStuff API")
register_exception_handlers(app)


@app.on_event("startup")
async def startup() -> None:
    await connect_db()


@app.on_event("shutdown")
async def shutdown() -> None:
    close_db()


@app.get("/api/v1/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


app.include_router(auth_router)
app.include_router(topics_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(interactions_router)
app.include_router(users_router)
