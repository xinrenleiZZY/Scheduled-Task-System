"""调度引擎：基于 APScheduler 的轮询式调度器。

- interval 模式：距上次运行达到 interval_seconds 即触发
- cron 模式：标准 5 字段 cron（分 时 日 月 周），支持 * / 整数 / 范围(-) / 列表(,) / 步长(/)
  周字段遵循标准语义：0 或 7 = 周日，1 = 周一 … 6 = 周六
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from croniter import croniter

from . import feishu, settings_service
from .config import settings
from .database import SessionLocal
from .emailer import send_mail
from .models import BotAccount, Chat, FeishuUser, SystemLog, Task, TaskLog

logger = logging.getLogger("scheduler")


# ==================== Cron 解析（标准 cron 语义） ====================
def validate_cron(expr: str) -> bool:
    """校验标准 5 字段 cron 表达式：分 时 日 月 周。"""
    expr = (expr or "").strip()
    if len(expr.split()) != 5:
        return False
    return bool(croniter.is_valid(expr))


def matches_cron(expr: str, now: datetime) -> bool:
    """判断 now（分钟粒度）是否命中 cron 表达式。"""
    expr = (expr or "").strip()
    if not validate_cron(expr):
        return False
    base = now.replace(second=0, microsecond=0)
    try:
        itr = croniter(expr, base - timedelta(seconds=1))
        return itr.get_next(datetime) == base
    except (ValueError, KeyError):
        return False


# ==================== 任务执行 ====================
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="task-exec")
_running: set[str] = set()
_running_lock = threading.Lock()


def _write_system_log(db, level: str, message: str, source: str = "scheduler") -> None:
    db.add(SystemLog(level=level, source=source, message=message[:2000]))


def _resolve_target(db, task: Task) -> tuple[str, str]:
    """返回 (目标ID, 错误信息)。目标ID 为空表示解析失败。"""
    if task.chat_type == "chat":
        chat = db.get(Chat, task.chat_id) if task.chat_id else None
        if not chat or not chat.chat_id:
            return "", "未配置目标群聊"
        return chat.chat_id, ""
    user = db.get(FeishuUser, task.chat_id) if task.chat_id else None
    if not user or not user.open_id:
        return "", "未配置目标用户"
    return user.open_id, ""


def execute_task(task_id: str, trigger: str = "schedule") -> tuple[bool, str]:
    """执行单个任务：发送飞书消息并落库统计与日志。"""
    with _running_lock:
        if task_id in _running:
            return False, "任务正在执行中"
        _running.add(task_id)
    start_ts = time.time()
    db = SessionLocal()
    ok = False
    msg = ""
    try:
        task = db.get(Task, task_id)
        if not task:
            return False, "任务不存在"

        text = task.message or "定时任务提醒"
        at_ids = list(task.at_user_ids or [])
        at_all = bool(task.at_all)

        if task.send_type == "api":
            bot = db.get(BotAccount, task.bot_id) if task.bot_id else None
            if not bot:
                ok, msg = False, "未找到应用机器人配置"
            else:
                target_id, err = _resolve_target(db, task)
                if not target_id:
                    ok, msg = False, err
                else:
                    ok, msg = feishu.api_send_text(
                        chat_id=target_id,
                        text=text,
                        at_user_ids=at_ids,
                        app_id=bot.app_id,
                        app_secret=bot.app_secret,
                    )
        else:
            webhook = task.webhook_url or _setting_value(db, "default_webhook_url") or settings.default_webhook_url
            secret = task.secret or _setting_value(db, "default_webhook_secret") or settings.default_webhook_secret
            if not webhook or not secret:
                ok, msg = False, "未配置 Webhook 或 Secret"
            else:
                ok, msg = feishu.webhook_send_text(webhook, secret, text, at_ids, at_all)

        duration = round(time.time() - start_ts, 2)
        status = "success" if ok else "fail"

        # 更新任务统计
        task.total_runs += 1
        if ok:
            task.success_count += 1
            task.last_error = ""
        else:
            task.fail_count += 1
            task.last_error = msg
        task.last_run_time = datetime.now()
        task.last_duration = duration
        task.last_status = status

        # 写任务日志
        if ok:
            db.add(TaskLog(task_id=task_id, status=status, duration=duration,
                           message=f"执行成功 | 耗时 {duration}s | 触发方式: {trigger}"))
        else:
            db.add(TaskLog(task_id=task_id, status=status, duration=duration,
                           message=f"执行失败 | 耗时 {duration}s | 错误: {msg}"))

        _write_system_log(db, "info" if ok else "error",
                          f"[{task.name}] {'执行成功' if ok else '执行失败: ' + msg}（{duration}s）")
        db.commit()

        # 错误报告邮件
        if not ok:
            _maybe_send_error_report(db, task, msg)

        return ok, msg
    except Exception as e:  # noqa: BLE001
        logger.exception("执行任务异常")
        db.rollback()
        return False, f"执行异常: {e}"
    finally:
        db.close()
        with _running_lock:
            _running.discard(task_id)


def _setting_value(db, key: str, default=""):
    return settings_service.get_one(db, key, default)


def _maybe_send_error_report(db, task: Task, error: str) -> None:
    if not settings_service.get_one(db, "err_report", False):
        return
    addr = settings_service.get_one(db, "err_email", settings.error_report_email)
    if not addr:
        return
    send_mail(
        to_addr=addr,
        subject=f"[{settings.app_name}] 定时任务执行失败 - {task.name}",
        body=f"任务: {task.name}（{task.id}）\n时间: {datetime.now():%Y-%m-%d %H:%M:%S}\n错误: {error}",
    )


# ==================== 调度判定 ====================
def _should_run(task: Task, now: datetime) -> bool:
    if task.schedule_type == "interval":
        if not task.last_run_time:
            return True
        return (now - task.last_run_time).total_seconds() >= max(1, task.interval_seconds)

    # cron 模式
    if not matches_cron(task.cron_expr, now):
        return False
    if not task.last_run_time:
        return True
    return task.last_run_time.strftime("%Y-%m-%d %H:%M") != now.strftime("%Y-%m-%d %H:%M")


_last_checked: dict[str, float] = {}


def tick() -> None:
    """一次调度轮询。"""
    now = datetime.now()
    now_ts = time.time()
    db = SessionLocal()
    try:
        tasks = db.query(Task).filter(Task.enabled.is_(True)).all()
        due: list[str] = []
        for task in tasks:
            if now_ts - _last_checked.get(task.id, 0) < settings.scheduler_interval_seconds - 1:
                continue
            if _should_run(task, now):
                due.append(task.id)
        # 先标记，避免同一轮重复
        for task_id in due:
            _last_checked[task_id] = now_ts
    finally:
        db.close()

    for task_id in due:
        _executor.submit(execute_task, task_id, "schedule")


def daily_backup() -> None:
    """每日自动备份（对应旧版 24h 备份逻辑）。"""
    db = SessionLocal()
    try:
        record = backup_service.create_backup(db, kind="auto", note="每日自动备份")
        _write_system_log(db, "info", f"每日自动备份完成: {record.filename}")
        db.commit()
    except Exception as e:  # noqa: BLE001
        logger.exception("每日备份失败")
    finally:
        db.close()


# ==================== 生命周期 ====================
_scheduler = BackgroundScheduler(timezone=settings.timezone)


def start() -> None:
    if _scheduler.running:
        return
    _scheduler.add_job(
        tick,
        trigger="interval",
        seconds=settings.scheduler_interval_seconds,
        id="task_poll",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _scheduler.add_job(
        daily_backup,
        trigger="cron",
        hour=3,
        minute=0,
        id="daily_backup",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("调度器已启动，轮询间隔 %ss", settings.scheduler_interval_seconds)


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
    _executor.shutdown(wait=False)
    logger.info("调度器已停止")
