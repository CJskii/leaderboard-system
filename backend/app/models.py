import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Table,
    func,
    Index,
    Enum,
)
from sqlalchemy.orm import relationship, Session

from .database import Base


class BugSeverity(str, enum.Enum):
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    participation_days = Column(Integer, default=0)
    role = Column(String, default="watson")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    elo_history = relationship("EloHistory", back_populates="user")
    reported_bugs = relationship("BugReport", back_populates="reporter")


class Contest(Base):
    __tablename__ = "contest"

    id = Column(Integer, primary_key=True, index=True)
    # TODO: remove default values for start and end date and adjust tests accordingly
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    date = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    participants = relationship("User", secondary="contest_participants")
    found_bugs = relationship("Bug", back_populates="contest")
    bug_reports = relationship("BugReport", back_populates="contest")


contest_participants = Table(
    "contest_participants",
    Base.metadata,
    Column("contest_id", Integer, ForeignKey("contest.id")),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("signup_date", DateTime, default=datetime.now(timezone.utc)),
)


class Bug(Base):
    __tablename__ = "bug"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    severity = Column(Enum(BugSeverity), nullable=False)
    reported_by_id = Column(Integer, ForeignKey("user.id"))
    contest_id = Column(Integer, ForeignKey("contest.id"))

    reported_by = relationship("User")
    contest = relationship("Contest", back_populates="found_bugs")
    reports = relationship("BugReport", back_populates="bug")


class BugReport(Base):
    __tablename__ = "bug_report"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    bug_id = Column(Integer, ForeignKey("bug.id"))
    contest_id = Column(Integer, ForeignKey("contest.id"))
    report_time = Column(DateTime, default=datetime.now(timezone.utc))

    reporter = relationship("User", back_populates="reported_bugs")
    bug = relationship("Bug", back_populates="reports")
    contest = relationship("Contest", back_populates="bug_reports")


class EloHistory(Base):
    __tablename__ = "elo_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    contest_id = Column(Integer, ForeignKey("contest.id"))
    elo_points_before = Column(Integer)
    elo_points_after = Column(Integer)
    change_reason = Column(String)

    user = relationship("User", back_populates="elo_history")
    contest = relationship("Contest")
    __table_args__ = (Index("idx_user_contest", "user_id", "contest_id"),)


def update_elo_points(user: User, contest: Contest, elo_change: int, session: Session):
    elo_before = calculate_current_elo(user.id, session)
    elo_after = elo_before + elo_change

    # Create a new EloHistory record
    elo_history_entry = EloHistory(
        user_id=user.id,
        contest_id=contest.id,
        elo_points_before=elo_before,
        elo_points_after=elo_after,
        change_reason="Contest participation",
    )

    session.add(elo_history_entry)
    session.commit()


def calculate_current_elo(user_id: int, session: Session) -> int:
    elo_points = (
        session.query(
            func.sum(EloHistory.elo_points_after - EloHistory.elo_points_before)
        )
        .filter(EloHistory.user_id == user_id)
        .scalar()
    )  # type: ignore

    return elo_points if elo_points is not None else 0
