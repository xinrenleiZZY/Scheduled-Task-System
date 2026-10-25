"""邮件发送（QQ 邮箱 SMTP），沿用旧版接口。"""
import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText

from .config import settings

logger = logging.getLogger("email")


def send_mail(to_addr: str, subject: str, body: str) -> tuple[bool, str]:
    if not settings.smtp_user or not settings.smtp_password:
        return False, "未配置发件邮箱（SMTP_USER / SMTP_PASSWORD）"
    if not to_addr:
        return False, "收件人不能为空"

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = settings.smtp_user
    msg["To"] = to_addr
    msg["Subject"] = Header(subject or "HZX-定时唤醒 邮件反馈", "utf-8")

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as s:
            s.starttls()
            s.login(settings.smtp_user, settings.smtp_password)
            s.sendmail(settings.smtp_user, [to_addr], msg.as_string())
        return True, "发送成功"
    except Exception as e:  # noqa: BLE001
        logger.exception("发送邮件失败")
        return False, f"发送失败: {e}"
