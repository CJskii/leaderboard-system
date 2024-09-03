from fastapi import HTTPException, status
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")

    participants = contest.participants
    if not participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No participants found for this contest")

    for user in participants:
        reported_bugs = db.query(models.BugReport).filter(
            models.BugReport.user_id == user.id,
            models.BugReport.contest_id == contest_id
        ).all()

        if reported_bugs:
            # Calculate ELO change
            elo_change = elo_service.calculate_elo_change(user, contest, reported_bugs, db)
            update_elo_points(db, user, contest, elo_change)
        else:
            # Apply participation penalty if the user found no bugs
            elo_service.apply_participation_penalty(user, contest, db)

    db.commit()
    return {"message": "ELO points processed for contest participants"}
