"""飞书用户/机器人接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FeishuUser
from ..schemas import ActionResult, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(FeishuUser).order_by(FeishuUser.name).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = FeishuUser(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.get(FeishuUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=ActionResult)
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(FeishuUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return ActionResult(success=True, message="用户已删除")
