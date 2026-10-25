"""系统配置：全部通过环境变量注入，避免硬编码密钥。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ===== 应用信息 =====
    app_name: str = "HZX-定时唤醒"
    app_version: str = "V5.3.0"
    developer: str = "IT-钟"
    phone: str = "18072740843"

    # ===== 数据库 =====
    database_url: str = "postgresql+psycopg2://hzx:hzx123456@localhost:5432/hzx_scheduler"

    # ===== 时区 / 调度 =====
    timezone: str = "Asia/Shanghai"
    scheduler_interval_seconds: int = 10

    # ===== 飞书默认 Webhook（可选，留空则必须由任务/设置提供）=====
    default_webhook_url: str = ""
    default_webhook_secret: str = ""

    # ===== 邮件（QQ 邮箱）=====
    smtp_host: str = "smtp.qq.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    error_report_email: str = ""

    # ===== 备份 =====
    data_dir: str = "/app/data"
    backup_keep_days: int = 30

    # ===== 服务 =====
    host: str = "0.0.0.0"
    port: int = 6100
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
