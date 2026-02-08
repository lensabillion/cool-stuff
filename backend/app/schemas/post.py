from pydantic import BaseModel, Field
from datetime import datetime

class PostCreateText(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

class PostUpdateText(BaseModel):
    body: str = Field(min_length=1, max_length=2000)

class PostOut(BaseModel):
    id: str
    topic_id: str
    created_by: str
    body: str
    created_at: datetime
    updated_at: datetime | None
    upvote_count: int = 0
    comment_count: int = 0
  
