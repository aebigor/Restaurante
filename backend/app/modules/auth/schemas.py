from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    terms_accepted: bool
    marketing_opt_in: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
