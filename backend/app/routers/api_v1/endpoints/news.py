"""
Gaming News and Esports Portal API endpoints.
Provides esports tournament coverage, game balance patch notes, and news feeds.
"""

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentAdminUser, DatabaseSession
from app.schemas.common import ApiResponse
from app.schemas.news import NewsArticleCreate, NewsArticleResponse
from app.services.news_service import NewsService

router = APIRouter()


@router.get(
    "",
    response_model=ApiResponse[list[NewsArticleResponse]],
    summary="Get Gaming News & Patch Notes Feed",
    description="Fetches latest esports news, tournament notices, and balance patches with game/category filtering.",
)
async def get_news_feed(
    db: DatabaseSession,
    game: str | None = Query(None, description="Filter by title (e.g. VALORANT, CS2, Apex, or All)"),
    category: str | None = Query(None, description="Filter by category (Esports, Patch Notes, Announcements, or All)"),
    limit: int = Query(20, ge=1, le=100),
):
    service = NewsService(db)
    articles = await service.get_articles(game=game, category=category, limit=limit)
    return ApiResponse.ok(data=articles, message=f"Retrieved {len(articles)} gaming news articles.")


@router.post(
    "",
    response_model=ApiResponse[NewsArticleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Publish News Article (Admin Only)",
    description="Publishes a new esports update or game patch note.",
)
async def create_news_article(
    payload: NewsArticleCreate,
    admin: CurrentAdminUser,
    db: DatabaseSession,
):
    service = NewsService(db)
    article = await service.create_article(payload)
    return ApiResponse.ok(data=article, message="News article published successfully.")
