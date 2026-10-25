"""仪表盘接口：全局统计 + 关注任务。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task
from ..schemas import DashboardOut, DashboardStats
from ..serializers import task_to_out

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    total = len(tasks)
    enabled = sum(1 for t in tasks if t.enabled)
    success = sum(t.success_count or 0 for t in tasks)
    fail = sum(t.fail_count or 0 for t in tasks)
    rate = round(success / (success + fail) * 100, 1) if (success + fail) else 0.0

    pinned = [task_to_out(t) for t in tasks if t.pinned]
    pinned.sort(key=lambda t: t.created_at, reverse=True)

    return DashboardOut(
        stats=DashboardStats(
            total_tasks=total,
            enabled_tasks=enabled,
            success_count=success,
            fail_count=fail,
            success_rate=rate,
        ),
        pinned_tasks=pinned,
    )
