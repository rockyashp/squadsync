"""
SQLAlchemy Models Package.
Exports all core models for centralized access and Alembic autogenerate discovery:
1. User (users)
2. GamerProfile (gamer_profiles)
3. GameAccount (game_accounts)
4. PlayerStat (player_stats)
5. SurveyAnswer (survey_answers)
6. GamerDNA (gamer_dna)
7. Friendship (friendships)
8. Team & TeamMember (teams, team_members)
9. ChatMessage (chat_messages)
10. NewsArticle (news_articles)
11. UserReport (user_reports)
"""

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.chat import ChatMessage
from app.models.friendship import Friendship, FriendshipStatus
from app.models.game_account import GameAccount
from app.models.gamer_dna import GamerDNA
from app.models.gamer_profile import GamerProfile
from app.models.news import NewsArticle
from app.models.player_stat import PlayerStat
from app.models.report import ReportStatus, UserReport
from app.models.survey_answer import SurveyAnswer, SurveyResponse
from app.models.team import Team, TeamMember
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "User",
    "GamerProfile",
    "GameAccount",
    "PlayerStat",
    "SurveyAnswer",
    "SurveyResponse",
    "GamerDNA",
    "Friendship",
    "FriendshipStatus",
    "Team",
    "TeamMember",
    "ChatMessage",
    "NewsArticle",
    "UserReport",
    "ReportStatus",
]
