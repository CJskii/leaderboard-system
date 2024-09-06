import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from ..app import models
from ..app.database import SessionLocal, engine
from ..app.models import contest_participants
from ..main import app

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()

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
        models.User(
            username="user3",
            email="user3@example.com",
            hashed_password="hashedpassword3",
            role="watson",
        ),
        models.User(
            username="user4",
            email="user4@example.com",
            hashed_password="hashedpassword4",
            role="watson",
        ),
    ]
    session.add_all(users)
    session.commit()

    start_date = datetime.now(timezone.utc) - timedelta(days=40)
    end_date = datetime.now(timezone.utc) - timedelta(days=30)
    contest = models.Contest(id=1, start_date=start_date, end_date=end_date)
    session.add(contest)
    session.commit()

    contest.participants.extend(users)
    session.commit()

    bugs = [
        models.Bug(
            severity="critical",
            description="Critical bug",
            reported_by_id=users[0].id,
            contest_id=contest.id,
        ),
        models.Bug(
            severity="high",
            description="High severity bug",
            reported_by_id=users[1].id,
            contest_id=contest.id,
        ),
        models.Bug(
            severity="medium",
            description="Medium severity bug",
            reported_by_id=users[2].id,
            contest_id=contest.id,
        ),
        models.Bug(
            severity="medium",
            description="Another Medium severity bug",
            reported_by_id=users[3].id,
            contest_id=contest.id,
        ),
    ]
    session.add_all(bugs)
    session.commit()

    bug_reports = [
        models.BugReport(user_id=users[0].id, bug_id=bugs[0].id, contest_id=contest.id),
        models.BugReport(user_id=users[1].id, bug_id=bugs[1].id, contest_id=contest.id),
        models.BugReport(user_id=users[2].id, bug_id=bugs[2].id, contest_id=contest.id),
        models.BugReport(user_id=users[3].id, bug_id=bugs[3].id, contest_id=contest.id),
    ]
    session.add_all(bug_reports)
    session.commit()

    yield session

    session.close()
    models.Base.metadata.drop_all(bind=engine)


# Test ELO processing with valid token
def test_process_elo_invalid_token(setup_database: Session):
    response = client.post(
        "/contests/1/process_elo", headers={"admin-token": "invalid_token"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin token."


# Test ELO processing with different severity bugs
def test_process_elo_with_elo_assertions(setup_database: Session):
    admin_token = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")
    contest_id = 1

    response = client.post(
        f"/contests/{contest_id}/process_elo", headers={"admin-token": admin_token}
    )

    assert response.status_code == 200
    assert "message" in response.json()

    session = setup_database
    users = session.query(models.User).all()

    elo_histories = {}
    for user in users:
        elo_history = (
            session.query(models.EloHistory)
            .filter_by(user_id=user.id)
            .order_by(models.EloHistory.id)
            .all()
        )
        assert (
            len(elo_history) > 0
        ), f"ELO history should be created for user {user.username}"
        elo_histories[user.username] = elo_history[-1].elo_points_after

    # Check that users with higher severity bugs gain more ELO
    assert (
        elo_histories["user1"] > elo_histories["user2"]
    ), "User with critical bug should gain more ELO than high severity bug."
    assert (
        elo_histories["user2"] > elo_histories["user3"]
    ), "User with high severity bug should gain more ELO than medium severity bug."
    assert (
        elo_histories["user3"] == elo_histories["user4"]
    ), "Users with same severity bugs should gain the same ELO."


# Test role updates after ELO processing
def test_update_user_roles_with_elo(setup_database: Session):
    admin_token = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")
    contest_id = 1

    response = client.post(
        f"/contests/{contest_id}/process_elo", headers={"admin-token": admin_token}
    )

    assert response.status_code == 200

    session = setup_database
    senior_watson = (
        session.query(models.User).filter(models.User.role == "senior_watson").all()
    )
    watson = session.query(models.User).filter(models.User.role == "watson").all()

    assert (
        len(senior_watson) == 4
    ), "All users should be assigned a higher role after ELO processing"
    assert (
        len(watson) == 0
    ), "All users should be assigned a higher role after ELO processing"


# Test participation days processing with invalid token
def test_process_participation_days_invalid_token(setup_database: Session):
    contest_id = 1

    response = client.post(
        f"/contests/{contest_id}/process_participation_days",
        headers={"admin-token": "invalid_token"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin token."


# Test contest with invalid ID
def test_process_participation_days_invalid_contest(setup_database: Session):
    admin_token = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")
    invalid_contest_id = 999

    response = client.post(
        f"/contests/{invalid_contest_id}/process_participation_days",
        headers={"admin-token": admin_token},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Contest not found"


# Test user without signup date
def test_process_participation_days_user_without_signup_date(setup_database: Session):
    admin_token = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")
    contest_id = 1

    session = setup_database
    users = session.query(models.User).all()

    session.execute(
        update(contest_participants)
        .where(contest_participants.c.user_id == users[0].id)
        .where(contest_participants.c.contest_id == contest_id)
        .values(signup_date=None)
    )
    session.commit()

    response = client.post(
        f"/contests/{contest_id}/process_participation_days",
        headers={"admin-token": admin_token},
    )

    assert response.status_code == 400
    assert "Signup date not found" in response.json()["detail"]


# Test contest still running
def test_process_participation_days_contest_still_running(setup_database: Session):
    admin_token = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")
    contest_id = 1

    session = setup_database
    contest = session.query(models.Contest).filter_by(id=contest_id).first()

    contest.end_date = datetime.now(timezone.utc) + timedelta(days=2)
    session.commit()

    # psql: datetime.now(timezone.utc) should be used instead of datetime.now()
    assert contest.end_date > datetime.now(), "Contest end_date should be in the future"

    users = session.query(models.User).all()

    signup_date = datetime.now(timezone.utc) - timedelta(days=10)
    for user in users:
        session.execute(
            update(contest_participants)
            .where(contest_participants.c.user_id == user.id)
            .where(contest_participants.c.contest_id == contest_id)
            .values(signup_date=signup_date)
        )
    session.commit()

    response = client.post(
        f"/contests/{contest_id}/process_participation_days",
        headers={"admin-token": admin_token},
    )

    assert (
        response.status_code == 400
    ), f"Expected 400, but got {response.status_code} instead"
    assert response.json()["detail"] == "Contest is still running"
