from pydantic import BaseModel, EmailStr, Field

class SignUpIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class SignInIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
