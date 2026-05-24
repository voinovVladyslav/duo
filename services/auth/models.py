from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class TimeStampedModel(SQLModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())


class User(TimeStampedModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)

    email: EmailStr = Field(max_length=200, unique=True)
    hashed_password: str = Field()
    password_updated_at: datetime | None = Field(default=None, nullable=True)
