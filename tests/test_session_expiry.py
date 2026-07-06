"""session 過期加固：新鮮的 token 有效，過期或偽造的一律拒絕。"""
import hashlib
import hmac
import time

from app import main


def test_fresh_session_is_valid():
    assert main._verify_session(main._sign_session("ap01")) == "ap01"


def test_expired_session_is_rejected():
    old_ts = int(time.time()) - (main.SESSION_MAX_AGE + 3600)
    payload = f"ap01.{old_ts}"
    sig = hmac.new(main.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    assert main._verify_session(f"{payload}.{sig}") is None  # 逾時應拒絕


def test_forged_session_is_rejected():
    assert main._verify_session("ap01") is None                    # 純明文
    assert main._verify_session("ap01.9999999999.deadbeef") is None  # 亂簽
