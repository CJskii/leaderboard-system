from pydantic import BaseModel

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    points: int
    participation_days: int
    role: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True

class Token (BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None