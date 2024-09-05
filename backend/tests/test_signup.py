import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ..app import models
from ..app.database import SessionLocal, engine
from ..app.models import contest_participants
from ..main import app

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        users = [
            models.User(
                username="user1",
                email="user1@example.com",
                hashed_password="hashedpassword1",
                role="watson",
            ),
            models.User(
                username="user2",
                email="user2@example.com",
                hashed_password="hashedpassword2",
                role="watson",
            ),
        ]
        session.add_all(users)
        session.commit()

        contest = models.Contest(
            start_date=datetime.now(timezone.utc) - timedelta(days=2),
            end_date=datetime.now(timezone.utc) + timedelta(days=2),
        )
        session.add(contest)
        session.commit()

        yield session
    finally:
        session.close()
        models.Base.metadata.drop_all(bind=engine)


# Valid signup
def test_valid_signup(setup_database):
    session = setup_database
    contest = session.query(models.Contest).first()
    user = session.query(models.User).first()

    response = client.post(f"/contests/{contest.id}/signup/{user.id}")
    assert response.status_code == 200
    assert response.json() == {"message": "User signed up for contest"}


# Invalid contest ID
def test_invalid_contest_id(setup_database):
    session = setup_database
    user = session.query(models.User).first()

    invalid_contest_id = 999
    response = client.post(f"/contests/{invalid_contest_id}/signup/{user.id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Contest not found"


# Invalid user ID
def test_invalid_user_id(setup_database):
    session = setup_database
    contest = session.query(models.Contest).first()

    invalid_user_id = 999
    response = client.post(f"/contests/{contest.id}/signup/{invalid_user_id}")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


# Contest already ended
def test_contest_already_ended(setup_database):
    session = setup_database
    contest = session.query(models.Contest).first()

    contest.end_date = datetime.now(timezone.utc) - timedelta(days=1)
    session.commit()

    user = session.query(models.User).first()
    response = client.post(f"/contests/{contest.id}/signup/{user.id}")
    assert response.status_code == 400
    assert "Contest has ended already" in response.json()["detail"]


# User already signed up for contest
def test_user_already_signed_up(setup_database):
    session = setup_database
    contest = session.query(models.Contest).first()
    user = session.query(models.User).first()

    session.execute(
        contest_participants.insert().values(
            contest_id=contest.id,
            user_id=user.id,
            signup_date=datetime.now(timezone.utc),
        )
    )
    session.commit()

    response = client.post(f"/contests/{contest.id}/signup/{user.id}")
    assert response.status_code == 400
    assert "User is already signed up for this contest" in response.json()["detail"]


# Contest not yet started (users can sign up before the contest begins)
def test_contest_not_started(setup_database):
    session = setup_database
    contest = session.query(models.Contest).first()

    contest.start_date = datetime.now(timezone.utc) + timedelta(days=5)
    contest.end_date = datetime.now(timezone.utc) + timedelta(days=10)
    session.commit()

    user = session.query(models.User).first()

    response = client.post(f"/contests/{contest.id}/signup/{user.id}")

    assert response.status_code == 200
    assert response.json() == {"message": "User signed up for contest"}


# Simulate a database failure
def test_database_failure_during_signup(monkeypatch, setup_database):
    session = setup_database
    contest = session.query(models.Contest).first()
    user = session.query(models.User).first()

    def mock_commit():
        raise Exception("Database failure")

    monkeypatch.setattr(Session, "commit", mock_commit)

    response = client.post(f"/contests/{contest.id}/signup/{user.id}")

    assert response.status_code == 400
    assert "Error during signup" in response.json()["detail"]
