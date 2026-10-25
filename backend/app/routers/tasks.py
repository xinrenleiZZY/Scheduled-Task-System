"""任务管理接口。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Task, TaskLog
from ..scheduler import execute_task, validate_cron
from ..schemas import ActionResult, TaskCreate, TaskLogOut, TaskOut, TaskUpdate
from ..serializers import task_to_out

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _validate_task_payload(data) -> None:
    schedule_type = getattr(data, "schedule_type", None)
    if schedule_type == "cron":
        expr = getattr(data, "cron_expr", "")
        if not validate_cron(expr):
            raise HTTPException(status_code=400, detail="Cron 表达式无效，格式应为：分 时 日 月 周（标准 cron，周：0/7=周日，1=周一 … 6=周六）")


@router.get("", response_model=list[TaskOut])
def list_tasks(
    enabled: bool | None = Query(default=None),
    pinned: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if enabled is not None:
        query = query.filter(Task.enabled.is_(enabled))
    if pinned is not None:
        query = query.filter(Task.pinned.is_(pinned))
    tasks = query.order_by(Task.created_at.desc()).all()
    return [task_to_out(t) for t in tasks]


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    _validate_task_payload(payload)
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_to_out(task)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task_to_out(task)


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    data = payload.model_dump(exclude_unset=True)
    if "schedule_type" in data and data["schedule_type"] == "cron" and not validate_cron(
        data.get("cron_expr", task.cron_expr)
    ):
        raise HTTPException(status_code=400, detail="Cron 表达式无效")
    for key, value in data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task_to_out(task)


@router.delete("/{task_id}", response_model=ActionResult)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return ActionResult(success=True, message="任务已删除")


@router.post("/{task_id}/toggle", response_model=TaskOut)
def toggle_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.enabled = not task.enabled
    db.commit()
    db.refresh(task)
    return task_to_out(task)


@router.post("/{task_id}/pin", response_model=TaskOut)
def toggle_pin(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.pinned = not task.pinned
    db.commit()
    db.refresh(task)
    return task_to_out(task)


@router.post("/{task_id}/run", response_model=ActionResult)
def run_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    ok, msg = execute_task(task_id, trigger="manual")
    return ActionResult(success=ok, message="触发成功" if ok else f"触发失败: {msg}")


@router.get("/{task_id}/logs", response_model=list[TaskLogOut])
def task_logs(task_id: str, limit: int = 200, db: Session = Depends(get_db)):
    if not db.get(Task, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    rows = (
        db.query(TaskLog)
        .filter(TaskLog.task_id == task_id)
        .order_by(TaskLog.ts.desc())
        .limit(limit)
        .all()
    )
    return rows


@router.delete("/{task_id}/logs", response_model=ActionResult)
def clear_task_logs(task_id: str, db: Session = Depends(get_db)):
    db.query(TaskLog).filter(TaskLog.task_id == task_id).delete()
    db.commit()
    return ActionResult(success=True, message="日志已清空")
