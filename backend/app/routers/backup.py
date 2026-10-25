"""备份 / 恢复 / 导入导出接口。"""
import os
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from .. import backup_service
from ..database import get_db
from ..models import BackupRecord
from ..schemas import ActionResult, BackupOut

router = APIRouter(prefix="/api/backups", tags=["backups"])


@router.get("", response_model=list[BackupOut])
def list_backups(db: Session = Depends(get_db)):
    return db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()


@router.post("", response_model=BackupOut, status_code=201)
def create_backup(note: str = "", db: Session = Depends(get_db)):
    return backup_service.create_backup(db, kind="manual", note=note)


@router.get("/export")
def export_now(db: Session = Depends(get_db)):
    """实时导出当前全部数据（不落盘）。"""
    return JSONResponse(content=backup_service.export_all(db))


@router.post("/import", response_model=ActionResult)
def import_now(payload: Any = Body(...), db: Session = Depends(get_db)):
    """导入数据。兼容本系统导出格式、旧版 settings.json（设置平铺）、旧版 tasks.json（顶层数组）。"""
    try:
        result = backup_service.import_data(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return ActionResult(success=True, message=f"导入完成: {result}")


@router.get("/{backup_id}/download")
def download_backup(backup_id: int, db: Session = Depends(get_db)):
    record = db.get(BackupRecord, backup_id)
    if not record:
        raise HTTPException(status_code=404, detail="备份不存在")
    path = os.path.join(backup_service.BACKUP_DIR, record.filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="备份文件已丢失")
    return FileResponse(path, media_type="application/json", filename=record.filename)


@router.post("/{backup_id}/restore", response_model=ActionResult)
def restore_backup(backup_id: int, db: Session = Depends(get_db)):
    record = db.get(BackupRecord, backup_id)
    if not record:
        raise HTTPException(status_code=404, detail="备份不存在")
    import json

    path = os.path.join(backup_service.BACKUP_DIR, record.filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="备份文件已丢失")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"备份文件无法解析: {e}") from e
    result = backup_service.import_data(db, data)
    return ActionResult(success=True, message=f"恢复完成: {result}")


@router.delete("/{backup_id}", response_model=ActionResult)
def delete_backup(backup_id: int, db: Session = Depends(get_db)):
    record = db.get(BackupRecord, backup_id)
    if not record:
        raise HTTPException(status_code=404, detail="备份不存在")
    path = os.path.join(backup_service.BACKUP_DIR, record.filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
    db.delete(record)
    db.commit()
    return ActionResult(success=True, message="备份已删除")
