import math
from app.models import calculate_current_elo, BugReport, EloHistory

duplicated_penality_multiplayer = 0.1 # All Watsons
invalid_report_penality = 10 # All Watsons
no_bugs_found_penality = 20 # Senior / Reserve Watson

class ELOService:
    def __init__(self, k_factor=32):
        self.k_factor = k_factor  # Determines the impact of each game on ELO rating

    @staticmethod
    def calculate_win_probability(user_elo, opponent_elo):
        return 1 / (1 + math.pow(10, (opponent_elo - user_elo) / 400))

    @staticmethod
    def get_opponent_elos(contest, user_id, session):
        opponent_elos = session.query(EloHistory.elo_points_after).select_from(BugReport).join(
            EloHistory, BugReport.user_id == EloHistory.user_id
        ).filter(
            BugReport.contest_id == contest.id,
            BugReport.user_id != user_id
        ).all()

        return [elo[0] for elo in opponent_elos if elo]

    @staticmethod
    def calculate_opponent_elo(opponent_elos):
        if opponent_elos:
            return sum(opponent_elos) / len(opponent_elos)
        return 100 # Default ELO value

    @staticmethod
    def get_severity_weight(severity):
        severity_weights = {
            'medium': 1.0,
            'high': 1.5,
            'critical': 2.0
        }
        return severity_weights.get(severity.lower(), 1.0)

    @staticmethod
    def get_duplicate_penalty(bug_report, session):
        duplicate_count = session.query(BugReport).filter(
            BugReport.bug_id == bug_report.bug_id,
            BugReport.user_id != bug_report.user_id
        ).count()

        penalty = duplicated_penality_multiplayer * duplicate_count
        return penalty

    def calculate_elo_change(self, user, contest, reported_bugs, session):
        user_elo = calculate_current_elo(user.id, session)
        opponent_elos = self.get_opponent_elos(contest, user.id, session)
        opponent_elo = self.calculate_opponent_elo(opponent_elos)

        total_elo_change = 0

        for bug_report in reported_bugs:
            severity_weight = self.get_severity_weight(bug_report.bug.severity)
            win_probability = self.calculate_win_probability(user_elo, opponent_elo)

            # Adjust ELO based on the league: Higher ELO users should gain less
            if user.role == 'senior_watson':
                adjusted_k_factor = self.k_factor * 0.75
            elif user.role == 'reserve_watson':
                adjusted_k_factor = self.k_factor * 0.9
            else:
                adjusted_k_factor = self.k_factor

            bug_value = severity_weight * (1 - win_probability)
            duplicate_penalty = self.get_duplicate_penalty(bug_report, session)
            bug_value -= duplicate_penalty

            total_elo_change += int(adjusted_k_factor * bug_value)

        return total_elo_change

    @staticmethod
    def apply_invalid_submission_penalty(user, contest, invalid_reports, session):
        penalty = invalid_report_penality * invalid_reports
        current_elo = calculate_current_elo(user.id, session)
        new_elo = max(current_elo - penalty, 0)

        elo_history_entry = EloHistory(
            user_id=user.id,
            contest_id=contest.id,
            elo_points_before=current_elo,
            elo_points_after=new_elo,
            change_reason="Penalty for invalid submissions"
        )

        session.add(elo_history_entry)
        session.commit()

    @staticmethod
    def apply_participation_penalty(user, contest, session):
        if user.role in ['senior_watson', 'reserve_watson']:
            others_found_bugs = session.query(BugReport).filter(
                BugReport.contest_id == contest.id,
                BugReport.user_id != user.id
            ).count()

            user_found_bugs = session.query(BugReport).filter(
                BugReport.user_id == user.id,
                BugReport.contest_id == contest.id
            ).count()

            if others_found_bugs > 0 and user_found_bugs == 0:
                penalty = no_bugs_found_penality
                current_elo = calculate_current_elo(user.id, session)
                new_elo = max(current_elo - penalty, 0)

                elo_history_entry = EloHistory(
                    user_id=user.id,
                    contest_id=contest.id,
                    elo_points_before=current_elo,
                    elo_points_after=new_elo,
                    change_reason=f"Penalty for {user.role} not finding bugs"
                )

                session.add(elo_history_entry)
                session.commit()
