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

def test_critical_bug_single_reporter(elo_service, default_leaderboard):
    """
    Test that an auditor who finds a critical bug alone receives maximum performance and a positive ELO change.
    """

def test_critical_bug_multiple_reporters_same_league(elo_service, default_leaderboard):
    """
    Test that performance is lower when multiple auditors from the same league report the same critical bug.
    """

def test_critical_bug_multiple_reporters_different_leagues(elo_service, default_leaderboard):
    """
    Test that performance is lowered correctly when multiple auditors from different leagues report the same critical bug.
    """

def test_high_bug_single_reporter(elo_service, default_leaderboard):
    """
    Test that an auditor who finds a high-severity bug alone receives the higher performance and ELO change.
    """

def test_high_bug_multiple_reporters_same_league(elo_service, default_leaderboard):
    """
    Test that performance is lowered when multiple auditors from the same league report the same high-severity bug.
    """

def test_high_bug_multiple_reporters_different_leagues(elo_service, default_leaderboard):
    """
    Test that performance is lowered correctly when multiple auditors from different leagues report the same high-severity bug.
    """

def test_medium_bug_single_reporter(elo_service, default_leaderboard):
    """
    Test that an auditor who finds a medium-severity bug alone receives the higher performance and ELO change.
    """

def test_medium_bug_multiple_reporters_same_league(elo_service, default_leaderboard):
    """
    Test that performance is lowered when multiple auditors from the same league report the same medium
    """

def test_medium_bug_multiple_reporters_different_leagues(elo_service, default_leaderboard):
    """
    Test that performance is lowered correctly when multiple auditors from different leagues report the same medium-severity bug.
    """

def test_mixed_severity_bugs_multiple_reporters(elo_service, default_leaderboard):
    """
    Test that performance for each auditor is calculated correctly when multiple auditors report bugs of different severities.
    """