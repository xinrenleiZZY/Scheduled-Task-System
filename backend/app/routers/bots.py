"""飞书应用机器人凭证接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BotAccount
from ..schemas import ActionResult, BotCreate, BotOut, BotUpdate

router = APIRouter(prefix="/api/bots", tags=["bots"])


@router.get("", response_model=list[BotOut])
def list_bots(db: Session = Depends(get_db)):
    return db.query(BotAccount).order_by(BotAccount.name).all()


@router.post("", response_model=BotOut, status_code=201)
def create_bot(payload: BotCreate, db: Session = Depends(get_db)):
    bot = BotAccount(**payload.model_dump())
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@router.put("/{bot_id}", response_model=BotOut)
def update_bot(bot_id: str, payload: BotUpdate, db: Session = Depends(get_db)):
    bot = db.get(BotAccount, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(bot, key, value)
    db.commit()
    db.refresh(bot)
    return bot


@router.delete("/{bot_id}", response_model=ActionResult)
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    bot = db.get(BotAccount, bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    db.delete(bot)
    db.commit()
    return ActionResult(success=True, message="机器人已删除")
