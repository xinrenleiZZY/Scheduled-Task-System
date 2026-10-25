"""应用设置读写（键值存储于 app_settings 表）。"""
from .config import settings
from .models import AppSetting


def _defaults() -> dict:
    return {
        "theme": "light",
        "auto_update": True,
        "update_source": "auto",
        "err_report": False,
        "err_email": settings.error_report_email,
        "default_webhook_url": settings.default_webhook_url,
        "default_webhook_secret": settings.default_webhook_secret,
    }


def get_all(db) -> dict:
    result = _defaults()
    for row in db.query(AppSetting).all():
        if row.value is not None:
            result[row.key] = row.value
    return result


def get_one(db, key: str, default=None):
    row = db.get(AppSetting, key)
    if row is None or row.value is None:
        if default is not None:
            return default
        return _defaults().get(key)
    return row.value


def set_many(db, data: dict) -> dict:
    allowed = set(_defaults().keys())
    for key, value in data.items():
        if key not in allowed or value is None:
            continue
        row = db.get(AppSetting, key)
        if row is None:
            db.add(AppSetting(key=key, value=value))
        else:
            row.value = value
    db.commit()
    return get_all(db)


def ensure_defaults(db) -> None:
    """首次启动时写入默认设置行。"""
    existing = {r.key for r in db.query(AppSetting.key).all()}
    changed = False
    for key, value in _defaults().items():
        if key not in existing:
            db.add(AppSetting(key=key, value=value))
            changed = True
    if changed:
        db.commit()
