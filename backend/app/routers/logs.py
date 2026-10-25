"""日志接口：系统日志 + 任务日志概览。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SystemLog, Task, TaskLog
from ..schemas import ActionResult, SystemLogOut

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("/system", response_model=list[SystemLogOut])
def system_logs(limit: int = Query(default=300, le=2000), db: Session = Depends(get_db)):
    return db.query(SystemLog).order_by(SystemLog.ts.desc()).limit(limit).all()


@router.delete("/system", response_model=ActionResult)
def clear_system_logs(db: Session = Depends(get_db)):
    db.query(SystemLog).delete()
    db.commit()
    return ActionResult(success=True, message="系统日志已清空")


@router.get("/tasks")
def task_log_overview(db: Session = Depends(get_db)):
    """返回每个任务的日志概览（对应旧版任务日志文件列表）。"""
    rows = (
        db.query(
            TaskLog.task_id,
            func.count(TaskLog.id).label("count"),
            func.max(TaskLog.ts).label("last_ts"),
        )
        .group_by(TaskLog.task_id)
        .all()
    )
    name_map = {t.id: t.name for t in db.query(Task.id, Task.name).all()}
    return [
        {
            "task_id": r.task_id,
            "task_name": name_map.get(r.task_id, "已删除任务"),
            "count": r.count,
            "last_ts": r.last_ts,
        }
        for r in rows
    ]
