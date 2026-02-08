from typing import Optional

from pydantic import BaseModel, Field


class PostUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    url: Optional[str] = None
