from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.dashboard.service import group_dashboard, personal_dashboard
from app.db.session import get_db
from app.models import User
from app.schemas.dashboard import GroupDashboard, PersonalDashboard


router = APIRouter(tags=["dashboards"])


@router.get("/dashboard/me", response_model=PersonalDashboard)
def get_personal_dashboard(
    response: Response,
    activity_limit: int = Query(default=5, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    return personal_dashboard(db, user.id, activity_limit)


@router.get("/groups/{group_id}/dashboard", response_model=GroupDashboard)
def get_group_dashboard(
    group_id: UUID,
    response: Response,
    activity_limit: int = Query(default=5, ge=1, le=20),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    response.headers["Cache-Control"] = "private, no-store"
    return group_dashboard(db, group_id, user.id, activity_limit, limit, offset)
