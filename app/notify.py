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


def _cfg(setting_key: str, env_key: str, default: str = "") -> str:
    """設定優先讀 DB（後台管理），DB 空才退回環境變數。"""
    val = store.read_setting(setting_key)
    return val if val else os.getenv(env_key, default)


def _email_map() -> dict[str, str]:
    """帳號→email 對照，格式：ap02=a@x.com,ap03=b@x.com。DB 優先、.env 後備。"""
    raw = _cfg("email_map", "EMAIL_MAP")
    out: dict[str, str] = {}
    for pair in raw.split(","):
        if "=" in pair:
            k, _, v = pair.partition("=")
            out[k.strip()] = v.strip()
    return out


def _smtp_conn() -> smtplib.SMTP:
    host = _cfg("smtp_host", "SMTP_HOST")
    port = int(_cfg("smtp_port", "SMTP_PORT", "25") or "25")
    smtp = smtplib.SMTP(host, port, timeout=10)
    user = _cfg("smtp_user", "SMTP_USER")
    if user:
        smtp.starttls()
        smtp.login(user, _cfg("smtp_password", "SMTP_PASSWORD"))
    return smtp


def send_digests() -> dict[str, Any]:
    """有 SMTP 主機 + email 對照才真的寄；否則只回站內預覽（不寄）。"""
    digests = compose_digests()
    host = _cfg("smtp_host", "SMTP_HOST")
    email_map = _email_map()
    if not host or not email_map:
        return {"sent": False, "reason": "尚未設定 SMTP 主機 / email 對照（請至系統管理後台），僅產生站內預覽。", "digests": digests}

    sent = 0
    sender = _cfg("smtp_from", "SMTP_FROM", "no-reply@cl-fee.local")
    with _smtp_conn() as smtp:
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


def send_test(to: str) -> dict[str, Any]:
    """後台『測試寄信』：寄一封測試信到指定 email，驗證 SMTP 設定。"""
    host = _cfg("smtp_host", "SMTP_HOST")
    if not host:
        return {"sent": False, "reason": "尚未設定 SMTP 主機。"}
    if not to:
        return {"sent": False, "reason": "請提供收件 email。"}
    sender = _cfg("smtp_from", "SMTP_FROM", "no-reply@cl-fee.local")
    msg = EmailMessage()
    msg["Subject"] = "[CL_FEE] SMTP 測試信"
    msg["From"] = sender
    msg["To"] = to
    msg.set_content("這是一封測試信，代表 CL_FEE 的 SMTP 設定可以正常寄出。")
    with _smtp_conn() as smtp:
        smtp.send_message(msg)
    return {"sent": True, "to": to}
