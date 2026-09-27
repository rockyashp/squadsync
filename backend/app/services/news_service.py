"""
Gaming News Service implementing esports journalism, patch notes feeds, and graceful degradation (NF-2.3).
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.schemas.news import NewsArticleCreate, NewsArticleResponse

DEFAULT_NEWS_SEEDS = [
    {
        "title": "VCT Masters 2026: Team Vitality Dominates Grand Finals",
        "summary": "Team Vitality claimed the championship title in a thrilling 3-2 series, showcasing unprecedented synergy and innovative agent compositions.",
        "content": "In an electrifying five-map grand final, Vitality proved the value of role adaptability and seamless communication, turning around an 0-2 deficit to claim the trophy.",
        "source_url": "https://playvalorant.com/news",
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800",
        "game": "VALORANT",
        "category": "Esports",
    },
    {
        "title": "Counter-Strike 2 Update: Sub-Tick Precision Enhancements & Map Balance",
        "summary": "Valve has deployed a major technical patch refining sub-tick animation responsiveness and tweaking Mirage and Inferno bomb site timings.",
        "content": "The latest patch brings refined network packet compression, reducing apparent peekers advantage while balancing smoke dissipation mechanics across all active duty maps.",
        "source_url": "https://store.steampowered.com/news/app/730",
        "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800",
        "game": "CS2",
        "category": "Patch Notes",
    },
    {
        "title": "Apex Legends Season 24: New Support Legend & Ranked Overhaul",
        "summary": "Respawn introduces a dynamic support legend capable of rapid squad re-positioning, alongside transparent tier promotion trials.",
        "content": "Season 24 redefines team play with dedicated tactical utility perks, aiming to bridge the gap between solo queue players and coordinated 3-stack squads.",
        "source_url": "https://ea.com/games/apex-legends/news",
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800",
        "game": "Apex Legends",
        "category": "Announcements",
    },
    {
        "title": "Six Invitational 2026: Regional Qualifiers Schedule Announced",
        "summary": "Ubisoft announces dates and brackets for the upcoming Six Invitational qualifiers across North America, Europe, and APAC.",
        "content": "The road to the hammer begins this November with 32 international squads competing for open qualifier slots.",
        "source_url": "https://rainbow6.com",
        "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800",
        "game": "Rainbow Six",
        "category": "Esports",
    },
    {
        "title": "Call of Duty Warzone: Weapon Balancing Patch 1.42 Notes",
        "summary": "Comprehensive tuning pass across assault rifles and SMGs to promote loadout diversity in competitive resurgence lobbies.",
        "content": "Recoil curves and damage falloff distances have been standardized to encourage strategic medium-range engagements.",
        "source_url": "https://callofduty.com",
        "image_url": "https://images.unsplash.com/photo-1552824722-ddab1374e622?w=800",
        "game": "Call of Duty",
        "category": "Patch Notes",
    }
]


class NewsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_default_articles_if_empty(self) -> None:
        """Seeds default articles if the news database is currently empty."""
        stmt = select(NewsArticle).limit(1)
        res = await self.db.execute(stmt)
        if res.scalar_one_or_none() is None:
            for item in DEFAULT_NEWS_SEEDS:
                article = NewsArticle(
                    title=item["title"],
                    summary=item["summary"],
                    content=item["content"],
                    source_url=item["source_url"],
                    image_url=item["image_url"],
                    game=item["game"],
                    category=item["category"],
                    published_at=datetime.now(timezone.utc),
                )
                self.db.add(article)
            await self.db.commit()

    async def get_articles(self, game: str | None = None, category: str | None = None, limit: int = 20) -> list[NewsArticleResponse]:
        """Fetches news articles filtered by game title and category."""
        await self.seed_default_articles_if_empty()

        stmt = select(NewsArticle).order_by(desc(NewsArticle.published_at)).limit(limit)
        if game and game.lower() != "all":
            stmt = stmt.where(NewsArticle.game.ilike(f"%{game.strip()}%"))
        if category and category.lower() != "all":
            stmt = stmt.where(NewsArticle.category.ilike(f"%{category.strip()}%"))

        res = await self.db.execute(stmt)
        articles = res.scalars().all()
        return [NewsArticleResponse.model_validate(a) for a in articles]

    async def create_article(self, payload: NewsArticleCreate) -> NewsArticleResponse:
        """Creates a new news article entry."""
        article = NewsArticle(
            title=payload.title,
            summary=payload.summary,
            content=payload.content,
            source_url=payload.source_url,
            image_url=payload.image_url,
            game=payload.game,
            category=payload.category,
            published_at=datetime.now(timezone.utc),
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        return NewsArticleResponse.model_validate(article)
