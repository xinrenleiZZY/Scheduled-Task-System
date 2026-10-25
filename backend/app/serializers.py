"""模型 -> 响应对象的序列化辅助。"""
from .models import Task
from .schemas import TaskOut, TaskStats


def build_task_stats(task: Task) -> TaskStats:
    total = task.total_runs or 0
    rate = round((task.success_count or 0) / total * 100, 1) if total else 0.0
    return TaskStats(
        total_runs=total,
        success_count=task.success_count or 0,
        fail_count=task.fail_count or 0,
        last_run_time=task.last_run_time,
        last_duration=task.last_duration or 0.0,
        last_status=task.last_status or "",
        last_error=task.last_error or "",
        success_rate=rate,
    )


def task_to_out(task: Task) -> TaskOut:
    return TaskOut(
        id=task.id,
        name=task.name,
        enabled=task.enabled,
        pinned=task.pinned,
        schedule_type=task.schedule_type,
        interval_seconds=task.interval_seconds,
        cron_expr=task.cron_expr,
        webhook_url=task.webhook_url,
        secret=task.secret,
        send_type=task.send_type,
        bot_id=task.bot_id,
        chat_id=task.chat_id,
        chat_type=task.chat_type,
        message=task.message,
        at_user_ids=list(task.at_user_ids or []),
        at_user_names=list(task.at_user_names or []),
        at_all=task.at_all,
        created_at=task.created_at,
        stats=build_task_stats(task),
    )
