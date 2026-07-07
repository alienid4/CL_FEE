"""催辦通知：把逾期/快到期項目彙整成每人一封的摘要。
- 站內預覽永遠可用（compose_digests）。
- 真正寄 email 需要 SMTP 設定（SMTP_HOST）與帳號→email 對照（EMAIL_MAP）；
  未設定時只回預覽，不會亂寄。
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Any

from app import store


def compose_digests() -> list[dict[str, Any]]:
    """依 owner 範圍取催辦項目，每位負責人彙整成一封摘要（主旨＋內文）。"""
    items = store.overdue_reminders()
    by_owner: dict[str, list[dict[str, Any]]] = {}
    for it in items:
        by_owner.setdefault(it.get("owner") or "(未指派)", []).append(it)
    digests = []
    kind = {"case": "案件", "contract": "合約", "project": "專案"}
    for owner, its in sorted(by_owner.items()):
        lines = [
            f"- [{'已逾期' if x['severity'] == 'overdue' else '快到期'}] "
            f"{kind.get(x['type'], x['type'])} {x['code']} {x['title']}（期限 {x['date']}）"
            for x in its
        ]
        digests.append({
            "owner": owner,
            "count": len(its),
            "subject": f"[催辦] 您有 {len(its)} 件待處理案件/合約/專案",
            "body": "以下項目已逾期或即將到期，請盡快處理：\n" + "\n".join(lines),
        })
    return digests


def _email_map() -> dict[str, str]:
    """帳號→email 對照，格式：EMAIL_MAP="ap02=a@x.com,ap03=b@x.com"。未設定則空。"""
    raw = os.getenv("EMAIL_MAP", "")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        if "=" in pair:
            k, _, v = pair.partition("=")
            out[k.strip()] = v.strip()
    return out


def send_digests() -> dict[str, Any]:
    """有 SMTP_HOST + EMAIL_MAP 才真的寄；否則只回預覽（不寄）。"""
    digests = compose_digests()
    host = os.getenv("SMTP_HOST")
    email_map = _email_map()
    if not host or not email_map:
        return {"sent": False, "reason": "未設定 SMTP_HOST / EMAIL_MAP，僅產生站內預覽。", "digests": digests}

    sent = 0
    port = int(os.getenv("SMTP_PORT", "25"))
    sender = os.getenv("SMTP_FROM", "no-reply@cl-fee.local")
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if os.getenv("SMTP_USER"):
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""))
        for d in digests:
            to = email_map.get(d["owner"])
            if not to:
                continue
            msg = EmailMessage()
            msg["Subject"] = d["subject"]
            msg["From"] = sender
            msg["To"] = to
            msg.set_content(d["body"])
            smtp.send_message(msg)
            sent += 1
    return {"sent": True, "count": sent, "digests": digests}
