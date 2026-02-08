from app.common.mongo import serialize_mongo, to_object_id
from app.common.pagination import normalize_pagination
from app.modules.auth.schemas import CurrentUser
from app.modules.users import repository


async def my_bookmarks(current_user: CurrentUser, skip: int, limit: int):
    skip, limit = normalize_pagination(skip, limit)
    post_ids = await repository.bookmarked_post_ids(to_object_id(current_user.id), skip, limit)
    if not post_ids:
        return []
    posts = await repository.posts_by_ids(post_ids)
    return [serialize_mongo(p) for p in posts]


async def my_feed(current_user: CurrentUser, skip: int, limit: int):
    skip, limit = normalize_pagination(skip, limit)
    topic_ids = await repository.subscription_topic_ids(to_object_id(current_user.id))
    if not topic_ids:
        return []
    posts = await repository.posts_by_topic_ids(topic_ids, skip, limit)
    return [serialize_mongo(p) for p in posts]
