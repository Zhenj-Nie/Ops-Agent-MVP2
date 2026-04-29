from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

from app.config import settings
from app.db import get_conn, now_iso


class FeishuNotifier:
    """飞书通知占位。

    默认：不真实发送，仅写 SQLite。
    配置 FEISHU_WEBHOOK_URL 后：向飞书机器人 Webhook 发送 text 消息。
    """

    def send_text(self, text: str, extra_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "msg_type": "text",
            "content": {"text": text},
        }
        if extra_payload:
            payload["extra"] = extra_payload

        status = "placeholder_saved"
        response_text = ""

        if settings.feishu_webhook_url:
            try:
                resp = requests.post(settings.feishu_webhook_url, json=payload, timeout=10)
                response_text = resp.text
                status = "sent" if resp.ok else f"failed_http_{resp.status_code}"
            except Exception as exc:
                response_text = str(exc)
                status = "failed_exception"

        with get_conn() as conn:
            conn.execute(
                """
                INSERT INTO notifications(channel, text, payload_json, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("feishu", text, json.dumps(payload, ensure_ascii=False), status, now_iso()),
            )

        return {"status": status, "response": response_text, "payload": payload}
