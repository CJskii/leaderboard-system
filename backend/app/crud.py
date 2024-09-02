from sqlalchemy.orm import Session
from . import models, schemas, auth

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

def update_user_elo(db: Session, user_id: int, elo_change: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.elo_rating += elo_change
        db.commit()
        db.refresh(user)
    return user

def create_contest_result(db: Session, contest_result: schemas.ContestResultCreate):
    db_contest_result = models.ContestResult(**contest_result.model_dump())
    db.add(db_contest_result)
    db.commit()
    db.refresh(db_contest_result)
    return db_contest_result