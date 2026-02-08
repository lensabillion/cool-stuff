from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import HTTPException


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail="Invalid id")
    return ObjectId(value)


def serialize_mongo(doc: dict[str, Any]) -> dict[str, Any]:
    data = dict(doc)
    if "_id" in data:
        data["id"] = str(data.pop("_id"))
    for field in ["created_by", "user_id", "topic_id", "post_id"]:
        if field in data and isinstance(data[field], ObjectId):
            data[field] = str(data[field])
    return data
