import pytest
from fastapi.testclient import TestClient
from main import app
from app.database import SessionLocal, engine
from app import models
import os

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    models.Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    users = [
        models.User(username="testuser", email="testuser@example.com", hashed_password="fakehashedpassword"),
        models.User(username="testuser1", email="testuser1@example.com", hashed_password="fakehashedpassword"),
        models.User(username="testuser2", email="testuser2@example.com", hashed_password="fakehashedpassword"),
    ]
    session.add_all(users)
    session.commit()

    contest = models.Contest(id=1)
    session.add(contest)
    session.commit()

    contest.participants.extend(users)
    session.commit()

    bugs = [
        models.Bug(severity="critical", description="Critical bug", reported_by_id=users[0].id, contest_id=contest.id),
        models.Bug(severity="high", description="High bug", reported_by_id=users[1].id, contest_id=contest.id),
        models.Bug(severity="medium", description="Medium bug", reported_by_id=users[2].id, contest_id=contest.id),
    ]
    session.add_all(bugs)
    session.commit()

    bug_reports = [
        models.BugReport(user_id=users[0].id, bug_id=bugs[0].id, contest_id=contest.id),
        models.BugReport(user_id=users[1].id, bug_id=bugs[1].id, contest_id=contest.id),
        models.BugReport(user_id=users[2].id, bug_id=bugs[2].id, contest_id=contest.id),
    ]
    session.add_all(bug_reports)
    session.commit()

    yield session

    session.close()
    models.Base.metadata.drop_all(bind=engine)


def test_process_elo(setup_database):
    admin_token = os.getenv("ADMIN_TOKEN", "your-secure-admin-token")
    print("Admin Token:", admin_token)
    contest_id = 1

    response = client.post(
        f"/contests/{contest_id}/process_elo",
        headers={"admin-token": admin_token}
    )
    print("Response Status Code:", response.status_code)
    print("Response Body:", response.json())

    assert response.status_code == 200
    assert "message" in response.json()

    session = setup_database
    users = session.query(models.User).all()
    for user in users:
        elo_history = session.query(models.EloHistory).filter_by(user_id=user.id).all()
        assert len(elo_history) > 0

def test_process_elo_invalid_token(setup_database):
    response = client.post(
        "/contests/1/process_elo",
        headers={"admin-token": "invalid_token"}
    )
    print("Response Status Code:", response.status_code)
    print("Response Body:", response.json())

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin token."
