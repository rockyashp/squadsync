"""
Automated unit & integration tests for Gaming News Portal.
"""

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_get_news_feed(client: AsyncClient):
    """Test fetching gaming news articles with default seeding."""
    res = await client.get("/api/v1/news")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    articles = data["data"]
    assert len(articles) >= 1
    assert "title" in articles[0]
    assert "game" in articles[0]


@pytest.mark.asyncio
async def test_filter_news_by_game(client: AsyncClient):
    """Test filtering news articles by game name."""
    res = await client.get("/api/v1/news?game=VALORANT")
    assert res.status_code == 200
    articles = res.json()["data"]
    assert all("valorant" in a["game"].lower() for a in articles)
