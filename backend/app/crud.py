from sqlalchemy.orm import Session
from . import models, schemas

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = user.password + "notreallyhashed"
    db_auditor = models.User(
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_auditor)
    db.commit()
    db.refresh(db_auditor)
    return db_auditor
