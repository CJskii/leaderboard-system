from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    username: str
    password: str
    email: str

class User(UserBase):
    id: int
    points: int
    participation_days: int
    role: str
    is_active: bool
    is_admin: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None