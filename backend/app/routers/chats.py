"""飞书群聊接口。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Chat
from ..schemas import ActionResult, ChatCreate, ChatOut, ChatUpdate

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def list_chats(db: Session = Depends(get_db)):
    return db.query(Chat).order_by(Chat.name).all()


@router.post("", response_model=ChatOut, status_code=201)
def create_chat(payload: ChatCreate, db: Session = Depends(get_db)):
    chat = Chat(**payload.model_dump())
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


@router.put("/{chat_id}", response_model=ChatOut)
def update_chat(chat_id: str, payload: ChatUpdate, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="群聊不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(chat, key, value)
    db.commit()
    db.refresh(chat)
    return chat


@router.delete("/{chat_id}", response_model=ActionResult)
def delete_chat(chat_id: str, db: Session = Depends(get_db)):
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="群聊不存在")
    db.delete(chat)
    db.commit()
    return ActionResult(success=True, message="群聊已删除")
