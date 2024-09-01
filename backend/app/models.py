from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    points = Column(Integer, default=0)
    participation_days = Column(Integer, default=0)
    role = Column(String, default="watson")
