"""
Admin Service implementing platform analytics, moderation oversight, and user management (BR-4, BR-6).
"""

import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.friendship import Friendship
from app.models.report import ReportStatus, UserReport
from app.models.survey_answer import SurveyAnswer
from app.models.team import Team
from app.models.user import User
from app.schemas.admin import PlatformAnalytics, UserReportCreate, UserReportResponse, UserStatusUpdate


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_analytics(self) -> PlatformAnalytics:
        """Computes platform-wide metrics for admin monitoring."""
        total_users = await self.db.scalar(select(func.count(User.id))) or 0
        active_users = await self.db.scalar(select(func.count(User.id)).where(User.is_active == True)) or 0
        total_squads = await self.db.scalar(select(func.count(Team.id))) or 0
        total_friendships = await self.db.scalar(select(func.count(Friendship.id))) or 0
        total_surveys = await self.db.scalar(select(func.count(func.distinct(SurveyAnswer.user_id)))) or 0
        pending_reports = await self.db.scalar(
            select(func.count(UserReport.id)).where(UserReport.status == ReportStatus.PENDING.value)
        ) or 0

        return PlatformAnalytics(
            total_users=total_users,
            active_users=active_users,
            total_squads=total_squads,
            total_surveys_completed=total_surveys,
            total_friendships=total_friendships,
            pending_reports=pending_reports,
        )

    async def list_users(self, query: str | None = None, limit: int = 50) -> list[dict]:
        """Lists users with profile tags for admin oversight."""
        stmt = select(User).options(selectinload(User.profile)).order_by(User.created_at.desc()).limit(limit)
        if query:
            clean_q = f"%{query.strip().lower()}%"
            stmt = stmt.where(User.username.ilike(clean_q) | User.email.ilike(clean_q))

        res = await self.db.execute(stmt)
        users = res.scalars().all()

        user_data = []
        for u in users:
            prof = u.profile
            user_data.append({
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "gamer_tag": prof.gamer_tag if prof else u.username,
                "is_active": u.is_active,
                "is_locked": u.is_locked,
                "is_admin": getattr(u, "is_admin", False),
                "created_at": u.created_at,
            })
        return user_data

    async def update_user_status(self, user_id: uuid.UUID, update: UserStatusUpdate) -> dict:
        """Modifies user status flags (activate/suspend/lock)."""
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if update.is_active is not None:
            user.is_active = update.is_active
        if update.is_locked is not None:
            user.is_locked = update.is_locked

        await self.db.commit()
        await self.db.refresh(user)
        return {
            "id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "is_locked": user.is_locked,
        }

    async def create_report(self, reporter_id: uuid.UUID, payload: UserReportCreate) -> UserReportResponse:
        """Files a conduct report against a player."""
        if reporter_id == payload.reported_user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot report yourself.")

        target = await self.db.get(User, payload.reported_user_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reported user not found.")

        report = UserReport(
            reporter_id=reporter_id,
            reported_user_id=payload.reported_user_id,
            reason=payload.reason,
            details=payload.details,
            status=ReportStatus.PENDING.value,
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return UserReportResponse.model_validate(report)

    async def list_reports(self, status_filter: str | None = None) -> list[UserReportResponse]:
        """Lists user moderation reports."""
        stmt = select(UserReport).options(
            selectinload(UserReport.reporter),
            selectinload(UserReport.reported_user)
        ).order_by(UserReport.created_at.desc())

        if status_filter and status_filter.upper() != "ALL":
            stmt = stmt.where(UserReport.status == status_filter.upper())

        res = await self.db.execute(stmt)
        reports = res.scalars().all()

        responses = []
        for r in reports:
            responses.append(
                UserReportResponse(
                    id=r.id,
                    reporter_id=r.reporter_id,
                    reporter_username=r.reporter.username if r.reporter else None,
                    reported_user_id=r.reported_user_id,
                    reported_username=r.reported_user.username if r.reported_user else None,
                    reason=r.reason,
                    details=r.details,
                    status=r.status,
                    created_at=r.created_at,
                )
            )
        return responses

    async def update_report_status(self, report_id: uuid.UUID, new_status: str) -> UserReportResponse:
        """Updates review status of a report (BR-6)."""
        report = await self.db.get(UserReport, report_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

        report.status = new_status.upper()
        await self.db.commit()
        await self.db.refresh(report)
        return UserReportResponse.model_validate(report)
