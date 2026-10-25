"""ORM 模型：任务、统计、飞书凭证、日志、设置、备份记录。"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def gen_id() -> str:
    """生成 12 位十六进制短 ID（与旧版 tasks.json 保持一致）。"""
    return uuid.uuid4().hex[:12]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(255), default="新任务")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)

    schedule_type: Mapped[str] = mapped_column(String(16), default="interval")  # interval | cron
    interval_seconds: Mapped[int] = mapped_column(Integer, default=86400)
    cron_expr: Mapped[str] = mapped_column(String(64), default="0 9 * * *")

    webhook_url: Mapped[str] = mapped_column(String(512), default="")
    secret: Mapped[str] = mapped_column(String(255), default="")

    send_type: Mapped[str] = mapped_column(String(16), default="webhook")  # webhook | api
    bot_id: Mapped[str] = mapped_column(String(32), default="")
    chat_id: Mapped[str] = mapped_column(String(64), default="")  # 关联 chats.id / feishu_users.id
    chat_type: Mapped[str] = mapped_column(String(16), default="chat")  # chat | user

    message: Mapped[str] = mapped_column(Text, default="定时任务提醒")
    at_user_ids: Mapped[list] = mapped_column(JSONB, default=list)
    at_user_names: Mapped[list] = mapped_column(JSONB, default=list)
    at_all: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # ===== 统计 =====
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    last_run_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_duration: Mapped[float] = mapped_column(Float, default=0.0)
    last_status: Mapped[str] = mapped_column(String(16), default="")
    last_error: Mapped[str] = mapped_column(Text, default="")

    logs: Mapped[list["TaskLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", passive_deletes=True
    )


class TaskLog(Base):
    __tablename__ = "task_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    status: Mapped[str] = mapped_column(String(16), default="")  # success | fail | info
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    message: Mapped[str] = mapped_column(Text, default="")

    task: Mapped["Task"] = relationship(back_populates="logs")


class BotAccount(Base):
    """飞书自建应用机器人凭证。"""

    __tablename__ = "bot_accounts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(255), default="")
    app_id: Mapped[str] = mapped_column(String(128), default="")
    app_secret: Mapped[str] = mapped_column(String(255), default="")
    open_id: Mapped[str] = mapped_column(String(128), default="")


class Chat(Base):
    """飞书群聊。"""

    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(255), default="")
    chat_id: Mapped[str] = mapped_column(String(128), default="")


class FeishuUser(Base):
    """飞书用户/机器人（私聊目标、@ 对象）。"""

    __tablename__ = "feishu_users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(255), default="")
    type: Mapped[str] = mapped_column(String(16), default="user")  # user | bot
    open_id: Mapped[str] = mapped_column(String(128), default="")


class AppSetting(Base):
    """键值型应用设置（theme / auto_update / err_report ...）。"""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[Any] = mapped_column(JSONB, nullable=True)


class SystemLog(Base):
    """系统级日志（调度器、接口异常等）。"""

    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    level: Mapped[str] = mapped_column(String(16), default="info")
    source: Mapped[str] = mapped_column(String(64), default="system")
    message: Mapped[str] = mapped_column(Text, default="")


class BackupRecord(Base):
    """备份记录。"""

    __tablename__ = "backup_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), default="")
    kind: Mapped[str] = mapped_column(String(32), default="manual")  # manual | auto | restore
    size: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    note: Mapped[str] = mapped_column(Text, default="")
