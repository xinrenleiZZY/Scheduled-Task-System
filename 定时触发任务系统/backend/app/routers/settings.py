"""应用设置接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import settings_service
from ..database import get_db
from ..schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def read_settings(db: Session = Depends(get_db)):
    return settings_service.get_all(db)


@router.put("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    return settings_service.set_many(db, data)
