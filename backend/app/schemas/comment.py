from pydantic import BaseModel, Field,  field_validator
from datetime import datetime
from pydantic.types import StrictStr
from app.schemas.base import StrictBaseModel


class CommentCreate(StrictBaseModel):
    body: StrictStr = Field(..., min_length=1, max_length=1000)

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Body must not be empty")
        return v
class CommentUpdate(StrictBaseModel):
    body: StrictStr = Field(..., min_length=1, max_length=1000)

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Body must not be empty")
        return v

class CommentOut(BaseModel):
    id: str
    post_id: str
    created_by: str
    body: str
    created_at: datetime
    updated_at: datetime | None
