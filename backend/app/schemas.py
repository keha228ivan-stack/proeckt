from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    department: str
    role: str
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    department: str
    role: str

    class Config:
        from_attributes = True


class CourseOut(BaseModel):
    id: int
    name: str
    description: str
    deadline: Optional[date] = None

    class Config:
        from_attributes = True
