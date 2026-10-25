"""Pydantic 数据模型（请求 / 响应）。"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== 任务 ====================
class TaskBase(BaseModel):
    name: str = "新任务"
    enabled: bool = True
    pinned: bool = False
    schedule_type: Literal["interval", "cron"] = "interval"
    interval_seconds: int = 86400
    cron_expr: str = "0 9 * * *"
    webhook_url: str = ""
    secret: str = ""
    send_type: Literal["webhook", "api"] = "webhook"
    bot_id: str = ""
    chat_id: str = ""
    chat_type: Literal["chat", "user"] = "chat"
    message: str = "定时任务提醒"
    at_user_ids: list[str] = Field(default_factory=list)
    at_user_names: list[str] = Field(default_factory=list)
    at_all: bool = False


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    pinned: Optional[bool] = None
    schedule_type: Optional[Literal["interval", "cron"]] = None
    interval_seconds: Optional[int] = None
    cron_expr: Optional[str] = None
    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    send_type: Optional[Literal["webhook", "api"]] = None
    bot_id: Optional[str] = None
    chat_id: Optional[str] = None
    chat_type: Optional[Literal["chat", "user"]] = None
    message: Optional[str] = None
    at_user_ids: Optional[list[str]] = None
    at_user_names: Optional[list[str]] = None
    at_all: Optional[bool] = None


class TaskStats(BaseModel):
    total_runs: int = 0
    success_count: int = 0
    fail_count: int = 0
    last_run_time: Optional[datetime] = None
    last_duration: float = 0.0
    last_status: str = ""
    last_error: str = ""
    success_rate: float = 0.0


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    stats: TaskStats


# ==================== 飞书机器人 ====================
class BotBase(BaseModel):
    name: str = ""
    app_id: str = ""
    app_secret: str = ""
    open_id: str = ""


class BotCreate(BotBase):
    pass


class BotUpdate(BaseModel):
    name: Optional[str] = None
    app_id: Optional[str] = None
    app_secret: Optional[str] = None
    open_id: Optional[str] = None


class BotOut(BotBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


# ==================== 群聊 ====================
class ChatBase(BaseModel):
    name: str = ""
    chat_id: str = ""


class ChatCreate(ChatBase):
    pass


class ChatUpdate(BaseModel):
    name: Optional[str] = None
    chat_id: Optional[str] = None


class ChatOut(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


# ==================== 用户 ====================
class UserBase(BaseModel):
    name: str = ""
    type: Literal["user", "bot"] = "user"
    open_id: str = ""


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal["user", "bot"]] = None
    open_id: Optional[str] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


# ==================== 日志 ====================
class TaskLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    ts: datetime
    status: str
    duration: float
    message: str


class SystemLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    level: str
    source: str
    message: str


# ==================== 设置 ====================
class SettingsOut(BaseModel):
    theme: str = "light"
    auto_update: bool = True
    update_source: str = "auto"
    err_report: bool = False
    err_email: str = ""
    default_webhook_url: str = ""
    default_webhook_secret: str = ""


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    auto_update: Optional[bool] = None
    update_source: Optional[str] = None
    err_report: Optional[bool] = None
    err_email: Optional[str] = None
    default_webhook_url: Optional[str] = None
    default_webhook_secret: Optional[str] = None


# ==================== 仪表盘 ====================
class DashboardStats(BaseModel):
    total_tasks: int = 0
    enabled_tasks: int = 0
    success_count: int = 0
    fail_count: int = 0
    success_rate: float = 0.0


class DashboardOut(BaseModel):
    stats: DashboardStats
    pinned_tasks: list[TaskOut]


# ==================== 邮件 ====================
class EmailSend(BaseModel):
    to_addr: str
    subject: str = ""
    body: str = ""


# ==================== 备份 ====================
class BackupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    kind: str
    size: int
    created_at: datetime
    note: str


class ActionResult(BaseModel):
    success: bool
    message: str
