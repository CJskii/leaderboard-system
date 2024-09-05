from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import desc, func, exists
from sqlalchemy.orm import Session

from . import models, schemas, auth
from .elo_service import ELOService
from .models import contest_participants

elo_service = ELOService()

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_elo_points(db: Session, user: models.User, contest: models.Contest, elo_change: int):
    models.update_elo_points(user, contest, elo_change, db)
    db.commit()
    db.refresh(user)

# TODO: optimize this function
def process_contest_elo(contest_id: int, db: Session):
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    participants = contest.participants
    if not participants:
        raise HTTPException(status_code=400, detail="No participants found for this contest")

    processed_participants = []

    for user in participants:
        reported_bugs = db.query(models.BugReport).filter(
            models.BugReport.user_id == user.id,
            models.BugReport.contest_id == contest_id
        ).all()

        if reported_bugs:
            elo_change = elo_service.calculate_elo_change(user, contest, reported_bugs, db)
            update_elo_points(db, user, contest, elo_change)
        else:
            elo_service.apply_participation_penalty(user, contest, db)

        processed_participants.append(user)

    db.commit()

    return processed_participants


def update_user_roles(users_to_update: list[models.User], db: Session ):
    leaderboard = db.query(models.User).join(models.EloHistory).group_by(models.User.id).order_by(
        desc(func.sum(models.EloHistory.elo_points_after))
    ).limit(100).all()

    senior_watsons = set([user.id for user in leaderboard[:30]])  # Top 1-30
    reserve_watsons = set([user.id for user in leaderboard[30:100]])  # Top 31-100

    users_to_update_roles = []

    for user in users_to_update:
        current_role = user.role
        if user.id in senior_watsons:
            new_role = "senior_watson"
        elif user.id in reserve_watsons:
            new_role = "reserve_watson"
        else:
            new_role = "watson"

        if current_role != new_role:
            user.role = new_role
            users_to_update_roles.append(user)

    if users_to_update_roles:
        db.bulk_save_objects(users_to_update_roles)
        db.commit()

    return users_to_update_roles


def signup_for_contest(user_id: int, contest_id: int, db: Session):
    signup_date = datetime.now(timezone.utc)

    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    if contest.end_date < signup_date:
        raise HTTPException(status_code=400, detail="Contest has ended already")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_signup = db.query(
        exists().where(
            contest_participants.c.user_id == user_id,
        ).where(
            contest_participants.c.contest_id == contest_id
        )
    ).scalar()

    if existing_signup:
        raise HTTPException(status_code=400, detail="User is already signed up for this contest")

    db.execute(
        contest_participants.insert().values(
            contest_id=contest_id,
            user_id=user_id,
            signup_date=signup_date
        )
    )

    db.commit()

def process_participation_days(contest_id: int, db: Session):
    contest = db.query(models.Contest).filter(models.Contest.id == contest_id).first()
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    end_date = contest.end_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if end_date > now:
        raise HTTPException(status_code=400, detail="Contest is still running")

    for user in contest.participants:
        signup_record = db.query(contest_participants).filter(
            contest_participants.c.user_id == user.id,
            contest_participants.c.contest_id == contest_id
        ).first()

        if signup_record is None or signup_record.signup_date is None:
            raise HTTPException(status_code=400, detail=f"Signup date not found for user {user.id}")

        signup_date = signup_record.signup_date
        if signup_date.tzinfo is None:
            signup_date = signup_date.replace(tzinfo=timezone.utc)

        participation_days = (end_date - signup_date).days + 1
        if participation_days < 0:
            participation_days = 0

        user.participation_days += participation_days
        db.add(user)

    db.commit()

