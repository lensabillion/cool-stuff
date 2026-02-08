from datetime import datetime

from pydantic import BaseModel, Field


class TopicCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=2, max_length=500)


class TopicResponse(BaseModel):
    id: str
    name: str
    description: str
    created_by: str
    created_at: datetime
    subscriber_count: int = 0
    post_count: int = 0
