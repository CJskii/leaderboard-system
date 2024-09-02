from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    elo_points = Column(Integer, default=0)
    participation_days = Column(Integer, default=0)
    role = Column(String, default="watson")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    contest_results = relationship("ContestResult", back_populates="user")


class Contest(Base):
    __tablename__ = "contest"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now(timezone.utc))

    participants = relationship("User", secondary="contest_participants")
    found_bugs = relationship("Bug", back_populates="contest")


contest_participants = Table(
    'contest_participants',
    Base.metadata,
    Column('contest_id', Integer, ForeignKey('contest.id')),
    Column('user_id', Integer, ForeignKey('user.id'))
)


class Bug(Base):
    __tablename__ = "bug"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    severity = Column(String)
    reported_by_id = Column(Integer, ForeignKey("user.id"))
    contest_id = Column(Integer, ForeignKey("contest.id"))

    reported_by = relationship("User")
    contest = relationship("Contest", back_populates="found_bugs")


class ContestResult(Base):
    __tablename__ = "contest_result"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    contest_id = Column(Integer, ForeignKey("contest.id"))
    score = Column(Integer)
    elo_change = Column(Integer)

    user = relationship("User", back_populates="contest_results")
    contest = relationship("Contest")
