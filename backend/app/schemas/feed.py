from pydantic import BaseModel
from app.schemas.post import PostOut

class FeedOut(BaseModel):
    items: list[PostOut]
    subscription_count: int
    reason_empty: str | None  # "no_subscriptions" | "no_posts" | None
