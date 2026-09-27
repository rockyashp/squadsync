"""
Admin Dashboard, User Moderation & Platform Analytics API endpoints (BR-4, BR-6).
"""

import uuid
from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentAdminUser, CurrentUser, DatabaseSession
from app.schemas.admin import PlatformAnalytics, ReportStatusUpdate, UserReportCreate, UserReportResponse, UserStatusUpdate
from app.schemas.common import ApiResponse
from app.services.admin_service import AdminService

router = APIRouter()


@router.get(
    "/analytics",
    response_model=ApiResponse[PlatformAnalytics],
    summary="Platform Analytics KPI Metrics (Admin Only)",
    description="Provides counts of registered gamers, active squads, survey completions, and pending moderation tickets.",
)
async def get_platform_analytics(
    admin: CurrentAdminUser,
    db: DatabaseSession,
):
    service = AdminService(db)
    metrics = await service.get_analytics()
    return ApiResponse.ok(data=metrics, message="Platform analytics retrieved successfully.")


@router.get(
    "/users",
    response_model=ApiResponse[list[dict]],
    summary="User Management Oversight (Admin Only)",
    description="Lists platform accounts with active/locked status and profile tags.",
)
async def list_users(
    admin: CurrentAdminUser,
    db: DatabaseSession,
    q: str | None = Query(None, description="Search username or email"),
    limit: int = Query(50, ge=1, le=100),
):
    service = AdminService(db)
    users = await service.list_users(query=q, limit=limit)
    return ApiResponse.ok(data=users, message=f"Retrieved {len(users)} users.")


@router.put(
    "/users/{user_id}/status",
    response_model=ApiResponse[dict],
    summary="Moderate User Account Status (Admin Only)",
    description="Updates account suspension or locking flags.",
)
async def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    admin: CurrentAdminUser,
    db: DatabaseSession,
):
    service = AdminService(db)
    updated = await service.update_user_status(user_id=user_id, update=payload)
    return ApiResponse.ok(data=updated, message="User status updated successfully.")


@router.post(
    "/reports",
    response_model=ApiResponse[UserReportResponse],
    status_code=status.HTTP_201_CREATED,
    summary="File Conduct Report Against Player",
    description="Submits a player conduct report for administrator review.",
)
async def report_user(
    payload: UserReportCreate,
    current_user: CurrentUser,
    db: DatabaseSession,
):
    service = AdminService(db)
    report = await service.create_report(reporter_id=current_user.id, payload=payload)
    return ApiResponse.ok(data=report, message="Report submitted for administrator review.")


@router.get(
    "/reports",
    response_model=ApiResponse[list[UserReportResponse]],
    summary="List Moderation Reports (Admin Only)",
    description="Lists moderation tickets submitted by players with status filtering.",
)
async def list_reports(
    admin: CurrentAdminUser,
    db: DatabaseSession,
    status_filter: str | None = Query(None, description="Filter by status: PENDING, RESOLVED, DISMISSED, or ALL"),
):
    service = AdminService(db)
    reports = await service.list_reports(status_filter=status_filter)
    return ApiResponse.ok(data=reports, message=f"Retrieved {len(reports)} moderation reports.")


@router.put(
    "/reports/{report_id}/status",
    response_model=ApiResponse[UserReportResponse],
    summary="Update Report Review Status (Admin Only)",
    description="Updates the resolution state of a moderation report adhering to BR-6 (48-hour SLA).",
)
async def update_report_status(
    report_id: uuid.UUID,
    payload: ReportStatusUpdate,
    admin: CurrentAdminUser,
    db: DatabaseSession,
):
    service = AdminService(db)
    updated = await service.update_report_status(report_id=report_id, new_status=payload.status)
    return ApiResponse.ok(data=updated, message=f"Report status updated to {payload.status}.")
