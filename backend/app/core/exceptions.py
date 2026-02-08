from fastapi import Request
from fastapi.responses import JSONResponse
from pymongo.errors import DuplicateKeyError

async def duplicate_key_handler(request: Request, exc: DuplicateKeyError):
    # You can customize message based on exc.details if you want
    return JSONResponse(
        status_code=409,
        content={"detail": "Duplicate key error"},
    )
