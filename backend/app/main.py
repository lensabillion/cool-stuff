from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from pymongo.errors import DuplicateKeyError

from app.core.database import ensure_indexes
from app.core.dependencies import get_current_user
from app.core.exceptions import duplicate_key_handler
from app.core.config import settings
from app.api.v1.router import router as api_router


app = FastAPI()

# ✅ Safe validation errors (no raw input reflected)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    safe_errors = []
    for e in exc.errors():
        loc = e.get("loc", [])
        # loc example: ("body", "email")
        field = ".".join([str(x) for x in loc if x not in ("body",)])
        safe_errors.append(
            {
                "field": field or "body",
                "message": e.get("msg", "Invalid value"),
            }
        )

    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": safe_errors},
    )


# ✅ CORS for Lovable + local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)

# ✅ Duplicate key -> 409
app.add_exception_handler(DuplicateKeyError, duplicate_key_handler)


@app.on_event("startup")
async def startup():
    await ensure_indexes()


@app.get("/protected")
async def protected(user=Depends(get_current_user)):
    return {"message": "you are authenticated", "user": user}
