"""
Automated unit & integration tests for Admin Dashboard, Analytics, and Moderation (BR-4, BR-6).
"""

import uuid
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin_user, get_current_user
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User


@pytest.mark.asyncio
async def test_admin_access_control_br4(authenticated_client: AsyncClient, mock_user: User):
    """Test BR-4: regular user is rejected with 403 from admin endpoints."""
    # mock_user is not an admin
    res = await authenticated_client.get("/api/v1/admin/analytics")
    assert res.status_code == 403
    assert "administrative" in res.json().get("message", res.json().get("detail", "")).lower()


@pytest.mark.asyncio
async def test_admin_analytics_and_users(client: AsyncClient, db_session: AsyncSession):
    """Test admin accessing analytics when authenticated as admin."""
    admin_user = User(
        id=uuid.uuid4(),
        username="super_admin",
        email="admin@squadsync.gg",
        password_hash=get_password_hash("AdminPass123!"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    # Override current user and admin user
    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_current_admin_user] = lambda: admin_user

    try:
        # 1. Fetch Analytics
        res = await client.get("/api/v1/admin/analytics")
        assert res.status_code == 200
        analytics = res.json()["data"]
        assert "total_users" in analytics
        assert "total_squads" in analytics
        assert analytics["total_users"] >= 1

        # 2. List Users
        users_res = await client.get("/api/v1/admin/users")
        assert users_res.status_code == 200
        assert len(users_res.json()["data"]) >= 1
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_current_admin_user, None)


@pytest.mark.asyncio
async def test_user_conduct_report_and_moderation_br6(authenticated_client: AsyncClient, db_session: AsyncSession, mock_user: User):
    """Test submitting a conduct report and updating review status (BR-6)."""
    reported = User(
        id=uuid.uuid4(),
        username="griefer_player",
        email="griefer@squadsync.gg",
        password_hash=get_password_hash("Pass1234!"),
        is_active=True,
    )
    db_session.add(reported)
    await db_session.commit()

    # 1. Submit report
    report_payload = {
        "reported_user_id": str(reported.id),
        "reason": "Griefing / AFK in ranked",
        "details": "Intentionally abandoned round 3 in competitive match.",
    }
    submit_res = await authenticated_client.post("/api/v1/admin/reports", json=report_payload)
    assert submit_res.status_code == 201
    report_id = submit_res.json()["data"]["id"]
    assert submit_res.json()["data"]["status"] == "PENDING"

    # 2. Admin reviews report
    admin_user = User(
        id=uuid.uuid4(),
        username="mod_admin",
        email="mod@squadsync.gg",
        password_hash=get_password_hash("AdminPass123!"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(admin_user)
    await db_session.commit()

    app.dependency_overrides[get_current_admin_user] = lambda: admin_user
    try:
        review_res = await authenticated_client.put(
            f"/api/v1/admin/reports/{report_id}/status",
            json={"status": "RESOLVED"}
        )
        assert review_res.status_code == 200
        assert review_res.json()["data"]["status"] == "RESOLVED"
    finally:
        app.dependency_overrides.pop(get_current_admin_user, None)
