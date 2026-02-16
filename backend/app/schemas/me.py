from datetime import datetime
from app.schemas.post import PostOut

class UpvotedPostItem(PostOut):
    upvoted_at: datetime | None = None
