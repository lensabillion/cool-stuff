from pydantic import BaseModel, EmailStr, Field
from pydantic.types import StrictStr
from app.schemas.base import StrictBaseModel


USERNAME_REGEX = r"^[a-zA-Z0-9_]{3,20}$"
class SignupIn(StrictBaseModel):
    username: StrictStr = Field(..., min_length=3, max_length=20, pattern=USERNAME_REGEX)
    email: EmailStr
    password: StrictStr = Field(..., min_length=8, max_length=128)

class LoginIn(StrictBaseModel):
    email: EmailStr
    password: StrictStr = Field(..., min_length=8, max_length=128)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    role: str
