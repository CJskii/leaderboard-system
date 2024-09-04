from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from . import models, schemas, auth
from .elo_service import ELOService

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

    update_user_roles(db, processed_participants)

    return processed_participants


def update_user_roles(db: Session, users_to_update: list[models.User]):
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

