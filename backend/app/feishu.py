"""飞书消息推送：Webhook（自定义机器人）+ 应用机器人 API。

沿用旧版签名与 @ 逻辑，仅去掉硬编码凭证。
"""
import base64
import hashlib
import hmac
import json
import logging
import time

import requests

logger = logging.getLogger("feishu")

DEFAULT_TIMEOUT = 15


# ==================== 签名 ====================
def gen_sign(timestamp: int, secret: str) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256)
    return base64.b64encode(hmac_code.digest()).decode("utf-8")


def _build_at_text(at_user_ids: list[str] | None, at_all: bool = False) -> str:
    """构造 <at> 标签，自动识别 open_id / user_id。"""
    parts: list[str] = []
    if at_all:
        parts.append("<at user_id='all'></at>")
    for uid in at_user_ids or []:
        uid = (uid or "").strip()
        if not uid:
            continue
        if uid.startswith("ou_"):
            parts.append(f"<at open_id='{uid}'>@{uid}</at>")
        else:
            parts.append(f"<at user_id='{uid}'>@{uid}</at>")
    return ("".join(parts) + " ") if parts else ""


# ==================== Webhook 方式 ====================
def webhook_send_text(
    webhook_url: str,
    secret: str,
    text: str,
    at_user_ids: list[str] | None = None,
    at_all: bool = False,
) -> tuple[bool, str]:
    if not webhook_url or not secret:
        return False, "未配置 Webhook 或 Secret"

    timestamp = int(time.time())
    payload = {
        "timestamp": str(timestamp),
        "sign": gen_sign(timestamp, secret),
        "msg_type": "text",
        "content": {"text": f"{_build_at_text(at_user_ids, at_all)}{text}"},
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=DEFAULT_TIMEOUT)
        data = resp.json()
        if data.get("code") == 0:
            return True, "发送成功"
        return False, f"飞书返回错误: {data.get('msg', '未知错误')}"
    except requests.exceptions.Timeout:
        return False, "请求超时（15秒）"
    except requests.exceptions.ConnectionError:
        return False, "网络连接失败"
    except Exception as e:  # noqa: BLE001
        return False, f"发送异常: {e}"


# ==================== 应用机器人 API 方式 ====================
def get_tenant_access_token(app_id: str, app_secret: str) -> tuple[bool, str]:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    try:
        resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            return True, data.get("tenant_access_token")
        return False, data.get("msg", "获取 token 失败")
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def api_send_text(
    chat_id: str,
    text: str,
    at_user_ids: list[str] | None = None,
    app_id: str = "",
    app_secret: str = "",
) -> tuple[bool, str]:
    if not app_id or not app_secret:
        return False, "未配置应用机器人 App ID / Secret"
    if not chat_id:
        return False, "未配置目标群聊/用户"

    ok, token = get_tenant_access_token(app_id, app_secret)
    if not ok:
        return False, f"获取token失败: {token}"

    elements: list[dict] = []
    for uid in at_user_ids or []:
        uid = (uid or "").strip()
        if uid:
            elements.append({"tag": "at", "user_id": uid})
    elements.append({"tag": "text", "text": f" {text}" if elements else text})

    post_content = {"zh_cn": {"title": "", "content": [elements]}}
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "post",
        "content": json.dumps(post_content, ensure_ascii=False),
    }
    receive_id_type = "chat_id" if chat_id.startswith("oc_") else "open_id"

    try:
        resp = requests.post(
            f"{url}?receive_id_type={receive_id_type}",
            json=payload,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        data = resp.json()
        if data.get("code") == 0:
            return True, "发送成功"
        return False, f"飞书返回错误: {data.get('msg', '未知错误')} (code: {data.get('code')})"
    except Exception as e:  # noqa: BLE001
        return False, f"发送异常: {e}"
