from pydantic import BaseModel, Field
from datetime import datetime

class TopicCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=300)

class TopicOut(BaseModel):
    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    subscriber_count: int = 0
    post_count: int = 0
