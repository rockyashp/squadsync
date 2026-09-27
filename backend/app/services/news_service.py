"""
Gaming News Service — NewsAPI.org integration with DB caching and graceful fallback.

Fetch strategy:
  1. If NEWS_API_KEY is set and cached articles are stale (> NEWS_CACHE_TTL_HOURS old),
     fetch fresh articles from NewsAPI and upsert them into the DB (deduplicated by URL).
  2. Serve articles from the local DB (fast, offline-capable).
  3. If DB is empty and API is unavailable, seed static fallback articles.

Admin-published articles (POST /news) always go straight to the DB and are served normally.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.news import NewsArticle
from app.schemas.news import NewsArticleCreate, NewsArticleResponse

logger = logging.getLogger("squadsync.news")

# ---------------------------------------------------------------------------
# NewsAPI query map — maps our game filter values to effective search terms
# ---------------------------------------------------------------------------
GAME_QUERY_MAP: dict[str, str] = {
    "VALORANT":      "VALORANT esports OR valorant game",
    "CS2":           "Counter-Strike 2 OR CS2 esports",
    "Apex Legends":  "Apex Legends esports OR apex legends season",
    "Rainbow Six":   "Rainbow Six Siege esports OR r6 siege",
    "Dota 2":        "Dota 2 esports OR dota2 patch",
    "Call of Duty":  "Call of Duty warzone OR cod esports",
    "General":       "esports gaming competitive multiplayer",
}

# Default broad query used when no game filter is given
DEFAULT_QUERY = (
    "VALORANT OR \"Counter-Strike 2\" OR \"Apex Legends\" OR \"Rainbow Six Siege\" "
    "OR \"Dota 2\" OR \"Call of Duty\" esports"
)

# Map category names to fragment keywords for display
CATEGORY_KEYWORD_MAP: dict[str, list[str]] = {
    "patch notes":   ["patch", "update", "hotfix", "balance", "nerf", "buff"],
    "esports":       ["tournament", "championship", "vct", "league", "invitational", "major"],
    "announcements": ["announce", "reveal", "season", "new", "launch", "trailer"],
}

# Static fallback seed articles (used only when API key is absent AND DB is empty)
DEFAULT_NEWS_SEEDS: list[dict[str, str]] = [
    {
        "title":      "VCT Masters 2026: Team Vitality Dominates Grand Finals",
        "summary":    "Team Vitality claimed the championship title in a thrilling 3-2 series, showcasing unprecedented synergy and innovative agent compositions.",
        "content":    "In an electrifying five-map grand final, Vitality proved the value of role adaptability and seamless communication, turning around an 0-2 deficit to claim the trophy.",
        "source_url": "https://playvalorant.com/news",
        "image_url":  "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800",
        "game":       "VALORANT",
        "category":   "Esports",
    },
    {
        "title":      "Counter-Strike 2 Update: Sub-Tick Precision Enhancements and Map Balance",
        "summary":    "Valve has deployed a major technical patch refining sub-tick animation responsiveness and tweaking Mirage and Inferno bomb site timings.",
        "content":    "The latest patch brings refined network packet compression, reducing apparent peekers advantage while balancing smoke dissipation mechanics across all active duty maps.",
        "source_url": "https://store.steampowered.com/news/app/730",
        "image_url":  "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800",
        "game":       "CS2",
        "category":   "Patch Notes",
    },
    {
        "title":      "Apex Legends Season 24: New Support Legend and Ranked Overhaul",
        "summary":    "Respawn introduces a dynamic support legend capable of rapid squad re-positioning, alongside transparent tier promotion trials.",
        "content":    "Season 24 redefines team play with dedicated tactical utility perks, aiming to bridge the gap between solo queue players and coordinated 3-stack squads.",
        "source_url": "https://ea.com/games/apex-legends/news",
        "image_url":  "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800",
        "game":       "Apex Legends",
        "category":   "Announcements",
    },
    {
        "title":      "Six Invitational 2026: Regional Qualifiers Schedule Announced",
        "summary":    "Ubisoft announces dates and brackets for the upcoming Six Invitational qualifiers across North America, Europe, and APAC.",
        "content":    "The road to the hammer begins this November with 32 international squads competing for open qualifier slots.",
        "source_url": "https://rainbow6.com",
        "image_url":  "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800",
        "game":       "Rainbow Six",
        "category":   "Esports",
    },
    {
        "title":      "Call of Duty Warzone: Weapon Balancing Patch 1.42 Notes",
        "summary":    "Comprehensive tuning pass across assault rifles and SMGs to promote loadout diversity in competitive resurgence lobbies.",
        "content":    "Recoil curves and damage falloff distances have been standardized to encourage strategic medium-range engagements.",
        "source_url": "https://callofduty.com",
        "image_url":  "https://images.unsplash.com/photo-1552824722-ddab1374e622?w=800",
        "game":       "Call of Duty",
        "category":   "Patch Notes",
    },
]


def _infer_category(title: str, description: str) -> str:
    text = (title + " " + (description or "")).lower()
    for category, keywords in CATEGORY_KEYWORD_MAP.items():
        if any(kw in text for kw in keywords):
            return category.title()
    return "Esports"


def _infer_game(title: str, description: str) -> str:
    text = (title + " " + (description or "")).lower()
    game_hints = {
        "VALORANT":      ["valorant", "vct"],
        "CS2":           ["counter-strike 2", "cs2", "csgo"],
        "Apex Legends":  ["apex legends", "apex"],
        "Rainbow Six":   ["rainbow six", "r6s", "r6 siege"],
        "Dota 2":        ["dota 2", "dota2"],
        "Call of Duty":  ["call of duty", "warzone", "cod"],
    }
    for game, hints in game_hints.items():
        if any(hint in text for hint in hints):
            return game
    return "General"


class NewsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_articles(
        self,
        game: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> list[NewsArticleResponse]:
        await self._refresh_from_newsapi_if_stale(game=game)

        stmt = select(NewsArticle).order_by(desc(NewsArticle.published_at)).limit(limit)

        if game and game.lower() not in ("all", ""):
            stmt = stmt.where(NewsArticle.game.ilike(f"%{game.strip()}%"))
        if category and category.lower() not in ("all", ""):
            stmt = stmt.where(NewsArticle.category.ilike(f"%{category.strip()}%"))

        res = await self.db.execute(stmt)
        articles = res.scalars().all()

        if not articles:
            await self._seed_static_fallbacks()
            res = await self.db.execute(stmt)
            articles = res.scalars().all()

        return [NewsArticleResponse.model_validate(a) for a in articles]

    async def create_article(self, payload: NewsArticleCreate) -> NewsArticleResponse:
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

    async def _refresh_from_newsapi_if_stale(self, game: str | None = None) -> None:
        if not settings.NEWS_API_KEY:
            return

        ttl = timedelta(hours=settings.NEWS_CACHE_TTL_HOURS)
        cutoff = datetime.now(timezone.utc) - ttl

        stmt = select(func.max(NewsArticle.published_at))
        result = await self.db.execute(stmt)
        latest_ts: datetime | None = result.scalar_one_or_none()

        if latest_ts and latest_ts.tzinfo is None:
            latest_ts = latest_ts.replace(tzinfo=timezone.utc)

        if latest_ts and latest_ts >= cutoff:
            logger.debug("News cache is fresh (latest: %s). Skipping NewsAPI fetch.", latest_ts)
            return

        logger.info("News cache stale — fetching from NewsAPI (game=%s).", game)
        articles = await self._fetch_from_newsapi(game=game)
        if articles:
            await self._upsert_articles(articles)

    async def _fetch_from_newsapi(self, game: str | None = None) -> list[dict[str, Any]]:
        if game and game.lower() not in ("all", ""):
            query = GAME_QUERY_MAP.get(game, DEFAULT_QUERY)
        else:
            query = DEFAULT_QUERY

        params = {
            "q":        query,
            "language": "en",
            "sortBy":   "publishedAt",
            "pageSize": 30,
            "apiKey":   settings.NEWS_API_KEY,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.NEWS_API_BASE_URL}/everything", params=params
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "NewsAPI HTTP error %s — serving from cache.", exc.response.status_code
            )
            return []
        except httpx.RequestError as exc:
            logger.warning("NewsAPI request failed: %s — serving from cache.", exc)
            return []

        raw_articles: list[dict] = data.get("articles", [])
        logger.info("NewsAPI returned %d articles.", len(raw_articles))

        normalized: list[dict[str, Any]] = []
        for raw in raw_articles:
            title: str = raw.get("title", "")
            if not title or title == "[Removed]":
                continue

            description: str = raw.get("description") or ""
            published_str    = raw.get("publishedAt", "")

            try:
                published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                published_at = datetime.now(timezone.utc)

            normalized.append({
                "title":        title,
                "summary":      description or title,
                "content":      raw.get("content") or "",
                "source_url":   raw.get("url") or "",
                "image_url":    raw.get("urlToImage") or "",
                "game":         _infer_game(title, description),
                "category":     _infer_category(title, description),
                "published_at": published_at,
            })

        return normalized

    async def _upsert_articles(self, articles: list[dict[str, Any]]) -> None:
        if not articles:
            return

        existing_stmt = select(NewsArticle.source_url).where(
            NewsArticle.source_url.isnot(None)
        )
        res = await self.db.execute(existing_stmt)
        existing_urls: set[str] = {row[0] for row in res.fetchall()}

        new_count = 0
        for data in articles:
            url = data.get("source_url") or ""
            if url and url in existing_urls:
                continue

            self.db.add(NewsArticle(
                id=uuid.uuid4(),
                title=data["title"],
                summary=data["summary"],
                content=data.get("content"),
                source_url=url or None,
                image_url=data.get("image_url") or None,
                game=data["game"],
                category=data["category"],
                published_at=data["published_at"],
            ))
            if url:
                existing_urls.add(url)
            new_count += 1

        if new_count:
            await self.db.commit()
            logger.info("Upserted %d new articles from NewsAPI.", new_count)

    async def _seed_static_fallbacks(self) -> None:
        logger.info("Seeding static fallback news articles.")
        for item in DEFAULT_NEWS_SEEDS:
            self.db.add(NewsArticle(
                title=item["title"],
                summary=item["summary"],
                content=item["content"],
                source_url=item["source_url"],
                image_url=item["image_url"],
                game=item["game"],
                category=item["category"],
                published_at=datetime.now(timezone.utc),
            ))
        await self.db.commit()
