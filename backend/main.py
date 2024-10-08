import os
from datetime import timedelta

import jwt
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .app import crud, models, schemas, auth
from .app.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# OAuth2 scheme for bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Default admin token - should be changed in production
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

def verify_admin_token(admin_token: str = Header(...)):
    if admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token.",
        )
    return True
@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/contests/{contest_id}/process_elo")
def process_elo(
    contest_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)  # Admin token check
):
    try:
        # TODO: review how to do this in one transaction
        # 1: Process ELO for all participants
        participants = crud.process_contest_elo(contest_id, db)
        # 2: Update user roles based on their new ELO rankings
        crud.update_user_roles(participants, db)
        return {"message": "ELO points and roles updated for contest participants"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error during processing: " + str(e))

@app.post("/contests/{contest_id}/process_participation_days")
def process_participation_days(
    contest_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_token)  # Admin token check
):
    crud.process_participation_days(contest_id, db)
    return {"message": "Participation days updated for contest participants"}

@app.post("/contests/{contest_id}/signup/{user_id}")
def signup_for_contest(
    contest_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.signup_for_contest(user_id, contest_id, db)
        return {"message": "User signed up for contest"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error during signup: " + str(e))


@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    auditors = crud.get_users(db, skip=skip, limit=limit)
    return auditors

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user