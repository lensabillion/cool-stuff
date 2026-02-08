from pydantic import BaseModel


class FeedParams(BaseModel):
    skip: int = 0
    limit: int = 20
