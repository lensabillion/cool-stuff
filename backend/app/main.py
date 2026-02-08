from fastapi import FastAPI
from app.db.mongo import init_mongo, close_mongo, get_auth_db
from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.services.auth_service import ensure_auth_indexes

app = FastAPI(title="CoolStuff API")

@app.on_event("startup")
async def startup_event():
    init_mongo()
    # Ensure auth DB indexes (unique email)
    await ensure_auth_indexes(get_auth_db())

@app.on_event("shutdown")
async def shutdown_event():
    close_mongo()

app.include_router(health_router)
app.include_router(auth_router)
