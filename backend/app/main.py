from fastapi import FastAPI, Depends
from app.core.database import auth_db, app_db
from app.core.dependencies import get_current_user
from app.api.v1.router import router as api_router
from app.core.database import ensure_indexes
from pymongo.errors import DuplicateKeyError
from app.core.exceptions import duplicate_key_handler

app = FastAPI()
app.include_router(api_router)
app.add_exception_handler(DuplicateKeyError, duplicate_key_handler)
@app.on_event("startup")
async def startup():
    await ensure_indexes()

@app.get("/protected")
async def protected(user=Depends(get_current_user)):
    return {"message": "you are authenticated", "user": user}
