"""FastAPI 应用入口。"""
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import scheduler, settings_service
from .config import settings
from .database import SessionLocal, init_db
from .routers import (
    backup,
    bots,
    chats,
    dashboard,
    email,
    logs,
    settings as settings_router,
    tasks,
    users,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


def _wait_for_db(retries: int = 30, delay: float = 2.0) -> None:
    from sqlalchemy import text

    from .database import engine

    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("数据库连接成功")
            return
        except Exception as e:  # noqa: BLE001
            logger.warning("数据库未就绪（第 %s 次）: %s", attempt, e)
            time.sleep(delay)
    raise RuntimeError("无法连接数据库，请检查 DATABASE_URL 与 PostgreSQL 服务状态")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _wait_for_db()
    init_db()
    db = SessionLocal()
    try:
        settings_service.ensure_defaults(db)
    finally:
        db.close()
    scheduler.start()
    logger.info("%s %s 已启动", settings.app_name, settings.app_version)
    yield
    scheduler.shutdown()
    logger.info("服务已关闭")


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    dashboard.router,
    tasks.router,
    bots.router,
    chats.router,
    users.router,
    logs.router,
    settings_router.router,
    backup.router,
    email.router,
):
    app.include_router(router)


@app.get("/api/health")
def health():
    return {"status": "ok", "name": settings.app_name, "version": settings.app_version}


@app.get("/api/app-info")
def app_info():
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "developer": settings.developer,
        "phone": settings.phone,
        "timezone": settings.timezone,
        "scheduler_interval_seconds": settings.scheduler_interval_seconds,
    }


# ===== 托管前端静态资源（Vite 构建产物）=====
if os.path.isdir(STATIC_DIR):
    _assets = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        index = os.path.join(STATIC_DIR, "index.html")
        candidate = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        if os.path.isfile(index):
            return FileResponse(index)
        return JSONResponse(status_code=404, content={"detail": "frontend not built"})
