from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    username: str
    password: str
    email: str

class User(UserBase):
    id: int
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

class ContestResultCreate(BaseModel):
    user_id: int
    contest_id: int
    score: int
    elo_change: int

    model_config = ConfigDict(from_attributes=True)


class EloHistoryCreate(BaseModel):
    user_id: int
    contest_id: int
    elo_points_before: int
    elo_points_after: int
    change_reason: str

    model_config = ConfigDict(from_attributes=True)
