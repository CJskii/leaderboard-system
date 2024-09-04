import pytest
from app.elo_service import ELOService
from app.models import User, Contest, Bug, BugReport, EloHistory
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine

@pytest.fixture(scope="function")
def elo_service():
    return ELOService()

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)  # Create tables
    session = SessionLocal()
    yield session  # Test session
    session.rollback()  # Rollback
    session.close()
    Base.metadata.drop_all(bind=engine)  # Drop the tables after the test

@pytest.fixture(scope="function")
def default_leaderboard(db_session: Session):
    users = [
        User(username="senior_watson", role="senior_watson"),
        User(username="reserve_watson", role="reserve_watson"),
        User(username="watson", role="watson"),
        User(username="another_senior_watson", role="senior_watson"),
        User(username="another_reserve_watson", role="reserve_watson"),
        User(username="another_watson", role="watson"),
    ]

    db_session.add_all(users)
    db_session.commit()

    return {user.username: user for user in users}

@pytest.fixture(scope="function")
def setup_past_contests(db_session: Session, default_leaderboard):
    users = default_leaderboard.values()

    past_contest = Contest()
    db_session.add(past_contest)
    db_session.commit()

    elo_changes = {
        "senior_watson": 1500,
        "reserve_watson": 1300,
        "watson": 1200,
        "another_senior_watson": 1400,
        "another_reserve_watson": 1250,
        "another_watson": 1100,
    }

    for user in users:
        elo_history_entry = EloHistory(
            user_id=user.id,
            contest_id=past_contest.id,
            elo_points_before=0,
            elo_points_after=elo_changes[user.username],
            change_reason="Initial ELO setup from past contest"
        )
        db_session.add(elo_history_entry)

    db_session.commit()

    return past_contest

def test_critical_bug_single_reporter(elo_service, default_leaderboard, db_session: Session):
    user = default_leaderboard["watson"]

    contest = Contest()
    bug = Bug(severity="critical", description="Critical bug description", reported_by_id=user.id,
              contest_id=contest.id)

    db_session.add(contest)
    db_session.add(bug)
    db_session.commit()

    bug_report = BugReport(user_id=user.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add(bug_report)
    db_session.commit()

    elo_change = elo_service.calculate_elo_change(user, contest, [bug_report], db_session)

    # Test if the ELO change is positive as expected
    assert elo_change > 0

def test_critical_bug_multiple_reporters_same_league(elo_service, default_leaderboard, db_session: Session):
    user1 = default_leaderboard["watson"]
    user2 = default_leaderboard["another_watson"]

    contest = Contest()
    bug = Bug(severity="critical", description="Critical bug description", reported_by_id=user1.id,
              contest_id=contest.id)
    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 == elo_change_user2  # Same league, should get the same ELO change

def test_critical_bug_multiple_reporters_different_leagues(elo_service, default_leaderboard, db_session: Session):
    user1 = default_leaderboard["senior_watson"]
    user2 = default_leaderboard["watson"]

    contest = Contest()
    bug = Bug(severity="critical", description="Critical bug description", reported_by_id=user1.id,
              contest_id=contest.id)
    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 < elo_change_user2  # Senior Watson should gain less ELO than Watson

def test_high_bug_single_reporter(elo_service, default_leaderboard, db_session: Session):
    user = default_leaderboard["watson"]
    contest = Contest()
    bug = Bug(severity="high", description="High severity bug", reported_by_id=user.id, contest_id=contest.id)

    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report = BugReport(user_id=user.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report])
    db_session.commit()

    elo_change = elo_service.calculate_elo_change(user, contest, [bug_report], db_session)
    assert elo_change > 0  # Ensure points are positive for reporting a high-severity bug

def test_high_bug_multiple_reporters_same_league(elo_service, default_leaderboard, db_session: Session):
    user1 = default_leaderboard["watson"]
    user2 = default_leaderboard["another_watson"]

    contest = Contest()
    bug = Bug(severity="high", description="High severity bug", reported_by_id=user1.id, contest_id=contest.id)
    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 == elo_change_user2  # Same league, should get the same ELO change

def test_high_bug_multiple_reporters_different_leagues(elo_service, default_leaderboard, db_session: Session):
    user1 = default_leaderboard["senior_watson"]
    user2 = default_leaderboard["watson"]

    contest = Contest()
    bug = Bug(severity="high", description="High severity bug", reported_by_id=user1.id, contest_id=contest.id)
    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 < elo_change_user2  # Senior Watson should gain less ELO than Watson

def test_medium_bug_single_reporter(elo_service, default_leaderboard, db_session: Session):
    user = default_leaderboard["watson"]
    contest = Contest()
    bug = Bug(severity="medium", description="Medium severity bug", reported_by_id=user.id, contest_id=contest.id)

    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report = BugReport(user_id=user.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report])
    db_session.commit()

    elo_change = elo_service.calculate_elo_change(user, contest, [bug_report], db_session)
    assert elo_change > 0  # Ensure points are positive for reporting a medium-severity bug

def test_medium_bug_multiple_reporters_same_league(elo_service, default_leaderboard, db_session: Session):
    user1 = default_leaderboard["watson"]
    user2 = default_leaderboard["another_watson"]

    contest = Contest()
    bug = Bug(severity="medium", description="Medium severity bug", reported_by_id=user1.id, contest_id=contest.id)
    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 == elo_change_user2  # Same league, should get the same ELO change

def test_medium_bug_multiple_reporters_different_leagues(elo_service, default_leaderboard, db_session: Session):
    user1 = default_leaderboard["senior_watson"]
    user2 = default_leaderboard["watson"]

    contest = Contest()
    bug = Bug(severity="medium", description="Medium severity bug", reported_by_id=user1.id, contest_id=contest.id)
    db_session.add_all([contest, bug])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 < elo_change_user2  # Senior Watson should gain less ELO than Watson

def test_mixed_severity_bugs_multiple_reporters(elo_service, default_leaderboard, setup_past_contests, db_session: Session):
    user1 = default_leaderboard["senior_watson"]
    user2 = default_leaderboard["watson"]

    contest = Contest()
    db_session.add(contest)
    db_session.commit()

    bug1 = Bug(severity="critical", description="Critical severity bug", reported_by_id=user1.id, contest_id=contest.id)
    bug2 = Bug(severity="high", description="High severity bug", reported_by_id=user2.id, contest_id=contest.id)
    bug3 = Bug(severity="medium", description="Medium severity bug", reported_by_id=user2.id, contest_id=contest.id)

    db_session.add_all([bug1, bug2, bug3])
    db_session.commit()

    bug_report1 = BugReport(user_id=user1.id, bug_id=bug1.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user2.id, bug_id=bug2.id, contest_id=contest.id)
    bug_report3 = BugReport(user_id=user2.id, bug_id=bug3.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2, bug_report3])
    db_session.commit()

    elo_change_user1 = elo_service.calculate_elo_change(user1, contest, [bug_report1], db_session)
    elo_change_user2 = elo_service.calculate_elo_change(user2, contest, [bug_report2, bug_report3], db_session)

    assert elo_change_user1 > 0
    assert elo_change_user2 > 0
    assert elo_change_user1 < elo_change_user2  # Senior Watson with critical bug should gain less ELO

# Test for Multiple Bugs Reported by the Same User
def test_multiple_bugs_reported_by_same_user(elo_service, default_leaderboard, db_session: Session):
    user = default_leaderboard["watson"]
    contest = Contest()

    bug1 = Bug(severity="medium", description="Medium severity bug", reported_by_id=user.id, contest_id=contest.id)
    bug2 = Bug(severity="high", description="High severity bug", reported_by_id=user.id, contest_id=contest.id)
    bug3 = Bug(severity="critical", description="Critical severity bug", reported_by_id=user.id, contest_id=contest.id)

    db_session.add_all([contest, bug1, bug2, bug3])
    db_session.commit()

    bug_report1 = BugReport(user_id=user.id, bug_id=bug1.id, contest_id=contest.id)
    bug_report2 = BugReport(user_id=user.id, bug_id=bug2.id, contest_id=contest.id)
    bug_report3 = BugReport(user_id=user.id, bug_id=bug3.id, contest_id=contest.id)

    db_session.add_all([bug_report1, bug_report2, bug_report3])
    db_session.commit()

    elo_change = elo_service.calculate_elo_change(user, contest, [bug_report1, bug_report2, bug_report3], db_session)
    assert elo_change > 0  # Ensure ELO points increase correctly based on multiple bug reports

def test_senior_watson_earns_less_elo(elo_service, default_leaderboard, db_session: Session):
    senior_user = default_leaderboard["senior_watson"]
    junior_user = default_leaderboard["watson"]

    contest = Contest()
    bug = Bug(severity="high", description="High severity bug", reported_by_id=senior_user.id, contest_id=contest.id)

    db_session.add_all([contest, bug])
    db_session.commit()

    # Both users report the same bug
    bug_report_senior = BugReport(user_id=senior_user.id, bug_id=bug.id, contest_id=contest.id)
    bug_report_junior = BugReport(user_id=junior_user.id, bug_id=bug.id, contest_id=contest.id)

    db_session.add_all([bug_report_senior, bug_report_junior])
    db_session.commit()

    elo_change_senior = elo_service.calculate_elo_change(senior_user, contest, [bug_report_senior], db_session)
    elo_change_junior = elo_service.calculate_elo_change(junior_user, contest, [bug_report_junior], db_session)

    assert elo_change_senior > 0
    assert elo_change_junior > 0
    assert elo_change_senior < elo_change_junior  # Senior Watson should gain less ELO


