"""User domain model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.core.constants import Role


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr = Field(..., description="User email address")
    role: Role = Field(..., description="User role")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User password (plain text)")


class UserUpdate(BaseModel):
    """Schema for updating user fields."""

    role: Optional[Role] = Field(None, description="Updated role")


class UserOut(UserBase):
    """Schema for user output (response)."""

    id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserInDB(BaseModel):
    """Schema for user as stored in database (includes hashed password)."""

    id: int
    email: EmailStr
    hashed_password: str
    role: Role
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
