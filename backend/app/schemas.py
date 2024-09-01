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

    class Config:
        from_attributes = True
