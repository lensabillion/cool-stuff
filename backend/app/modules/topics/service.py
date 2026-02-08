from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.common.mongo import now_utc, serialize_mongo, to_object_id
from app.common.pagination import normalize_pagination
from app.common.utils import Role
from app.modules.auth.schemas import CurrentUser
from app.modules.topics import repository
from app.modules.topics.schemas import TopicCreateRequest, TopicResponse


async def create_topic(payload: TopicCreateRequest, current_user: CurrentUser) -> TopicResponse:
    doc = {
        "name": payload.name,
        "description": payload.description,
        "created_by": to_object_id(current_user.id),
        "created_at": now_utc(),
        "subscriber_count": 0,
        "post_count": 0,
    }
    result = await repository.create_topic(doc)
    doc["_id"] = result.inserted_id
    return TopicResponse(**serialize_mongo(doc))


async def list_topics(q: str | None, skip: int, limit: int):
    skip, limit = normalize_pagination(skip, limit)
    query = {"$text": {"$search": q}} if q else {}
    docs = await repository.list_topics(query, skip, limit)
    return [serialize_mongo(d) for d in docs]


async def subscribe(topic_id: str, current_user: CurrentUser):
    topic_oid = to_object_id(topic_id)
    if not await repository.get_topic(topic_oid):
        raise HTTPException(status_code=404, detail="Topic not found")
    try:
        await repository.create_subscription(
            {"user_id": to_object_id(current_user.id), "topic_id": topic_oid, "created_at": now_utc()}
        )
    except DuplicateKeyError:
        return {"subscribed": True}
    await repository.inc_topic_subscriber_count(topic_oid, 1)
    return {"subscribed": True}


async def unsubscribe(topic_id: str, current_user: CurrentUser):
    topic_oid = to_object_id(topic_id)
    res = await repository.delete_subscription(to_object_id(current_user.id), topic_oid)
    if res.deleted_count:
        await repository.inc_topic_subscriber_count(topic_oid, -1)
    return {"subscribed": False}


async def delete_topic(topic_id: str, current_user: CurrentUser):
    topic_oid = to_object_id(topic_id)
    if not await repository.get_topic(topic_oid):
        raise HTTPException(status_code=404, detail="Topic not found")

    if current_user.role != Role.admin:
        others = await repository.other_subscriber_count(topic_oid, to_object_id(current_user.id))
        if others > 0:
            raise HTTPException(status_code=403, detail="Cannot delete topic with other subscribers")

    post_ids = await repository.post_ids_by_topic(topic_oid)
    await repository.cascade_delete_posts(post_ids)
    await repository.delete_posts_by_topic(topic_oid)
    await repository.delete_subscriptions_by_topic(topic_oid)
    await repository.delete_topic(topic_oid)
    return {"deleted": True}
