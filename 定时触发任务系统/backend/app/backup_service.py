"""备份 / 恢复 / 导入导出服务（对应旧版 backup 目录 + restore_from_backup）。"""
import json
import os
from datetime import datetime, timedelta

from . import settings_service
from .config import settings
from .models import BackupRecord, BotAccount, Chat, FeishuUser, Task

BACKUP_DIR = os.path.join(settings.data_dir, "backup")
_DT_FMT = "%Y-%m-%d %H:%M:%S"


def ensure_dir() -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "enabled": task.enabled,
        "pinned": task.pinned,
        "schedule_type": task.schedule_type,
        "interval_seconds": task.interval_seconds,
        "cron_expr": task.cron_expr,
        "webhook_url": task.webhook_url,
        "secret": task.secret,
        "send_type": task.send_type,
        "bot_id": task.bot_id,
        "chat_id": task.chat_id,
        "chat_type": task.chat_type,
        "message": task.message,
        "at_user_ids": list(task.at_user_ids or []),
        "at_user_names": list(task.at_user_names or []),
        "at_all": task.at_all,
        "created_at": task.created_at.strftime(_DT_FMT) if task.created_at else "",
        "stats": {
            "total_runs": task.total_runs,
            "success_count": task.success_count,
            "fail_count": task.fail_count,
            "last_run_time": task.last_run_time.strftime(_DT_FMT) if task.last_run_time else "",
            "last_duration": task.last_duration,
            "last_status": task.last_status,
            "last_error": task.last_error,
        },
    }


def export_all(db) -> dict:
    """导出全部业务数据（对应旧版 settings.json + tasks.json）。"""
    return {
        "exported_at": datetime.now().strftime(_DT_FMT),
        "version": settings.app_version,
        "settings": settings_service.get_all(db),
        "tasks": [_task_to_dict(t) for t in db.query(Task).all()],
        "bot_accounts": [
            {"id": b.id, "name": b.name, "app_id": b.app_id, "app_secret": b.app_secret, "open_id": b.open_id}
            for b in db.query(BotAccount).all()
        ],
        "chats": [
            {"id": c.id, "name": c.name, "chat_id": c.chat_id} for c in db.query(Chat).all()
        ],
        "users": [
            {"id": u.id, "name": u.name, "type": u.type, "open_id": u.open_id}
            for u in db.query(FeishuUser).all()
        ],
    }


def create_backup(db, kind: str = "manual", note: str = "") -> BackupRecord:
    ensure_dir()
    data = export_all(db)
    filename = f"backup_{datetime.now():%Y-%m-%d_%H%M%S}.json"
    path = os.path.join(BACKUP_DIR, filename)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(payload)

    record = BackupRecord(
        filename=filename,
        kind=kind,
        size=len(payload.encode("utf-8")),
        note=note or f"{kind} 备份",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    clean_old(db)
    return record


def clean_old(db, max_days: int | None = None) -> None:
    """删除超过保留天数的备份文件与记录。"""
    max_days = max_days or settings.backup_keep_days
    ensure_dir()
    deadline = datetime.now() - timedelta(days=max_days)
    for fname in os.listdir(BACKUP_DIR):
        fpath = os.path.join(BACKUP_DIR, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            if datetime.fromtimestamp(os.path.getmtime(fpath)) < deadline:
                os.remove(fpath)
        except OSError:
            pass
    db.query(BackupRecord).filter(BackupRecord.created_at < deadline).delete()
    db.commit()


_SETTING_KEYS = {
    "theme",
    "auto_update",
    "update_source",
    "err_report",
    "err_email",
    "default_webhook_url",
    "default_webhook_secret",
}


def normalize_import(data) -> tuple[dict, list]:
    """兼容多种来源格式，统一成 {settings, tasks, bot_accounts, chats, users}。

    支持三类输入：
      1. 本系统导出格式：{settings, tasks, bot_accounts, chats, users}
      2. 旧版程序的 settings.json：设置项平铺在顶层（theme / err_email ...）
      3. 旧版程序的 tasks.json：顶层即任务数组
    """
    normalized = {"settings": {}, "tasks": [], "bot_accounts": [], "chats": [], "users": []}
    pinned: list = []

    if isinstance(data, list):
        normalized["tasks"] = [x for x in data if isinstance(x, dict)]
        return normalized, pinned

    if not isinstance(data, dict):
        raise ValueError("导入数据必须是 JSON 对象或数组")

    for key in _SETTING_KEYS:
        if data.get(key) is not None:
            normalized["settings"][key] = data[key]

    if isinstance(data.get("settings"), dict):
        for key in _SETTING_KEYS:
            if data["settings"].get(key) is not None:
                normalized["settings"][key] = data["settings"][key]

    for key in ("tasks", "bot_accounts", "chats", "users"):
        value = data.get(key)
        if isinstance(value, list):
            normalized[key] = [x for x in value if isinstance(x, dict)]

    if isinstance(data.get("pinned_tasks"), list):
        pinned = [x for x in data["pinned_tasks"] if isinstance(x, str)]

    return normalized, pinned


def import_data(db, data) -> dict:
    """导入 / 合并数据：列表按 id 去重，已存在则更新；设置直接覆盖。"""
    normalized, pinned = normalize_import(data)
    result = {"tasks": 0, "bot_accounts": 0, "chats": 0, "users": 0, "settings": 0, "pinned": 0}

    if normalized["settings"]:
        settings_service.set_many(db, normalized["settings"])
        result["settings"] = len(normalized["settings"])

    for item in normalized["bot_accounts"]:
        bot = db.get(BotAccount, item.get("id")) if item.get("id") else None
        if bot is None:
            bot = BotAccount(id=item.get("id") or None)
            db.add(bot)
        bot.name = item.get("name", bot.name or "")
        bot.app_id = item.get("app_id", bot.app_id or "")
        bot.app_secret = item.get("app_secret", bot.app_secret or "")
        bot.open_id = item.get("open_id", bot.open_id or "")
        result["bot_accounts"] += 1

    for item in normalized["chats"]:
        chat = db.get(Chat, item.get("id")) if item.get("id") else None
        if chat is None:
            chat = Chat(id=item.get("id") or None)
            db.add(chat)
        chat.name = item.get("name", chat.name or "")
        chat.chat_id = item.get("chat_id", chat.chat_id or "")
        result["chats"] += 1

    for item in normalized["users"]:
        user = db.get(FeishuUser, item.get("id")) if item.get("id") else None
        if user is None:
            user = FeishuUser(id=item.get("id") or None)
            db.add(user)
        user.name = item.get("name", user.name or "")
        user.type = item.get("type", user.type or "user")
        user.open_id = item.get("open_id", user.open_id or "")
        result["users"] += 1

    for item in normalized["tasks"]:
        _import_task(db, item)
        result["tasks"] += 1

    for pid in pinned:
        task = db.get(Task, pid)
        if task is not None and not task.pinned:
            task.pinned = True
            result["pinned"] += 1

    db.commit()
    return result


def _import_task(db, item: dict) -> None:
    tid = item.get("id")
    task = db.get(Task, tid) if tid else None
    if task is None:
        task = Task(**({"id": tid} if tid else {}))
        db.add(task)
    stats = item.get("stats", {}) if isinstance(item.get("stats"), dict) else {}
    for field in ("name", "schedule_type", "cron_expr", "webhook_url", "secret",
                  "send_type", "bot_id", "chat_id", "chat_type", "message"):
        if field in item:
            setattr(task, field, item[field])
    for field in ("enabled", "pinned", "at_all"):
        if field in item:
            setattr(task, field, bool(item[field]))
    if "interval_seconds" in item:
        task.interval_seconds = int(item["interval_seconds"] or 0)
    if isinstance(item.get("at_user_ids"), list):
        task.at_user_ids = item["at_user_ids"]
    if isinstance(item.get("at_user_names"), list):
        task.at_user_names = item["at_user_names"]
    if item.get("created_at"):
        try:
            task.created_at = datetime.strptime(item["created_at"], _DT_FMT)
        except ValueError:
            pass
    if stats:
        task.total_runs = int(stats.get("total_runs", 0) or 0)
        task.success_count = int(stats.get("success_count", 0) or 0)
        task.fail_count = int(stats.get("fail_count", 0) or 0)
        task.last_duration = float(stats.get("last_duration", 0) or 0)
        task.last_status = stats.get("last_status", "") or ""
        task.last_error = stats.get("last_error", "") or ""
        if stats.get("last_run_time"):
            try:
                task.last_run_time = datetime.strptime(stats["last_run_time"], _DT_FMT)
            except ValueError:
                pass
