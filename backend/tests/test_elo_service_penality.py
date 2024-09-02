import pytest
from app.elo_service import EloService, calculate_auditor_performance


@pytest.fixture(scope="function")
def elo_service():
    return EloService(k=32)

@pytest.fixture(scope="function")
def default_leaderboard():
    return {
        1: 1200,  # Auditor 1
        2: 1300,  # Auditor 2
        3: 1400,  # Auditor 3
    }

def test_invalid_submission_watson_penalty(elo_service, default_leaderboard):
    """Test that a Watson receives a low performance penalty for submitting an invalid bug report."""

def test_invalid_submission_reserve_watson_penalty(elo_service, default_leaderboard):
    """Test that a Reserve Watson receives a medium performance penalty for submitting an invalid bug report."""

def test_invalid_submission_senior_watson_penalty(elo_service, default_leaderboard):
    """Test that a Senior Watson receives a high performance penalty for submitting an invalid bug report."""

def test_watson_no_finding_penalty(elo_service, default_leaderboard):
    """Test that a Watson who does not report any bugs is not penalized."""

def test_senior_watson_no_finding(elo_service, default_leaderboard):
    """Test that a Senior Watson who does not report any bugs receives a high performance penalty."""

def test_reserve_watson_no_finding(elo_service, default_leaderboard):
    """Test that a Reserve Watson who does not report any bugs receives a medium performance penalty."""




