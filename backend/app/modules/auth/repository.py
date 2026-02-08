from app.core.database import get_auth_db


async def create_user(user_doc: dict):
    return await get_auth_db().users.insert_one(user_doc)


async def find_by_username_or_email(username_or_email: str):
    return await get_auth_db().users.find_one(
        {"$or": [{"username": username_or_email}, {"email": username_or_email}]}
    )
