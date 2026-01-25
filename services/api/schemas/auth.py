from pydantic import BaseModel, EmailStr, SecretStr


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class JsonWebToken(BaseModel):
    access_token: str
    token_type: str
    issued_at: float
    expired_at: float


