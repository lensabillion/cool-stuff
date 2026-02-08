from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentUpdateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)
