from pydantic import BaseModel, Field,  field_validator
from datetime import datetime
from pydantic.types import StrictStr
from app.schemas.base import StrictBaseModel

TOPIC_REGEX = r"^[a-zA-Z0-9 _-]{2,40}$"

class TopicCreate(StrictBaseModel):
    name: StrictStr = Field(..., min_length=2, max_length=40, pattern=TOPIC_REGEX)
    description: StrictStr | None = Field(default=None, max_length=300)

    @field_validator("description")
    @classmethod
    def desc_strip_if_present(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v if v else None


class TopicOut(BaseModel):
    id: str
    name: str
    description: str | None
    created_by: str
    created_at: datetime
    subscriber_count: int = 0
    post_count: int = 0
