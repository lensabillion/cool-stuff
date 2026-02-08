from pydantic import BaseModel, Field
from datetime import datetime

class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)

class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=1000)

class CommentOut(BaseModel):
    id: str
    post_id: str
    created_by: str
    body: str
    created_at: datetime
    updated_at: datetime | None
