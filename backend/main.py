from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/users/", response_model=list[schemas.User])
def read_auditors(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    auditors = crud.get_users(db, skip=skip, limit=limit)
    return auditors

@app.post("/users/", response_model=schemas.User)
def create_auditor(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)
