"""邮件反馈接口。"""
from fastapi import APIRouter

from ..emailer import send_mail
from ..schemas import ActionResult, EmailSend

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/send", response_model=ActionResult)
def send_email(payload: EmailSend):
    ok, msg = send_mail(payload.to_addr, payload.subject, payload.body)
    return ActionResult(success=ok, message=msg)
