"""
Data access repository layer package.
Exports standard SQLAlchemy 2.0 repositories adhering to the Repository Pattern.
"""

from app.repositories.base import BaseRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.dna_repository import DNARepository
from app.repositories.game_account_repository import GameAccountRepository
from app.repositories.player_stat_repository import PlayerStatRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.survey_repository import SurveyRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ProfileRepository",
    "GameAccountRepository",
    "PlayerStatRepository",
    "SurveyRepository",
    "DNARepository",
    "CandidateRepository",
]
