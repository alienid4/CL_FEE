from contextlib import asynccontextmanager
import csv
import hashlib
import hmac
import io
import os
from pathlib import Path
import secrets
import subprocess
import time
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.dev_console import console_status, run_console_command
from app.seed_data import clear_demo_data, demo_counts, load_demo_data
from app.import_mapping import mapping_draft_catalog
from app.settings import get_settings
from app.store import (
    approve_case,
    case_360,
    cases_needing_attention,
    cio_overview,
    submit_case,
    confirm_import_batch_cases_dry_run,
    expiring_contracts,
    create_import_batch,
    dashboard_summary,
    delete_row,
    disable_row,
    get_import_batch,
    initialize_database,
    insert_row,
    list_import_batches,
    list_import_rows,
    list_audit_logs,
    list_rows,
    monthly_spending_summary,
    preflight_import_batch_confirm,
    preview_import_mapping,
    search_records,
    set_current_actor,
    set_owner_scope,
    stage_import_rows,
    update_row,
)


def _load_dotenv(env_path: Path | None = None) -> None:
    """極簡 .env 載入器（無外部依賴）：把 .env 的鍵值放進環境變數。
    用 setdefault，所以已存在的環境變數（測試/正式環境已設定者）優先，不被覆寫。"""
    env_path = env_path or (Path(__file__).resolve().parent.parent / ".env")
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


_load_dotenv()


class CaseIn(BaseModel):
    case_code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    owner: str = ""
    status: str = "draft"
    amount: float = 0
    risk_level: str = "normal"
    note: str = ""
    next_step: str = ""


class CasePatch(BaseModel):
    case_code: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1)
    owner: str | None = None
    status: str | None = None
    amount: float | None = None
    risk_level: str | None = None
    note: str | None = None
    next_step: str | None = None


class ContractIn(BaseModel):
    contract_code: str = Field(min_length=1)
    contract_name: str = Field(min_length=1)
    vendor_name: str = ""
    amount: float | None = 0
    status: str = "active"
    case_id: int | None = None
    end_date: str = ""

    @field_validator("amount")
    @classmethod
    def _amount_default(cls, v: float | None) -> float:
        # 前端金額留空會送 null；視為 0，避免使用者不填金額就存不進去
        return 0.0 if v is None else v


class ContractPatch(BaseModel):
    contract_code: str | None = Field(default=None, min_length=1)
    contract_name: str | None = Field(default=None, min_length=1)
    vendor_name: str | None = None
    amount: float | None = None
    status: str | None = None
    case_id: int | None = None
    end_date: str | None = None


class PaymentIn(BaseModel):
    contract_id: int
    payment_month: str = Field(pattern=r"^\d{4}-\d{2}$")
    payment_amount: float
    invoice_status: str = "not_received"
    status: str = "pending"


class PaymentPatch(BaseModel):
    contract_id: int | None = None
    payment_month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    payment_amount: float | None = None
    invoice_status: str | None = None
    status: str | None = None


class DocumentIn(BaseModel):
    file_name: str = Field(min_length=1)
    document_type: str = "other"
    source_note: str = ""
    status: str = "active"
    case_id: int | None = None
    contract_id: int | None = None


class DocumentPatch(BaseModel):
    file_name: str | None = Field(default=None, min_length=1)
    document_type: str | None = None
    source_note: str | None = None
    status: str | None = None
    case_id: int | None = None
    contract_id: int | None = None


class BudgetIn(BaseModel):
    budget_code: str = Field(min_length=1)
    category: str = ""
    unit_name: str = ""
    fiscal_year: str = ""
    amount: float = 0
    status: str = "active"
    case_id: int | None = None
    note: str = ""


class BudgetPatch(BaseModel):
    budget_code: str | None = Field(default=None, min_length=1)
    category: str | None = None
    unit_name: str | None = None
    fiscal_year: str | None = None
    amount: float | None = None
    status: str | None = None
    case_id: int | None = None
    note: str | None = None


class ProjectIn(BaseModel):
    project_code: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    source: str = ""
    necessity: str = ""
    progress: float = 0
    owner: str = ""
    status: str = "active"
    case_id: int | None = None
    note: str = ""


class ProjectPatch(BaseModel):
    project_code: str | None = Field(default=None, min_length=1)
    project_name: str | None = Field(default=None, min_length=1)
    source: str | None = None
    necessity: str | None = None
    progress: float | None = None
    owner: str | None = None
    status: str | None = None
    case_id: int | None = None
    note: str | None = None


class SignoffIn(BaseModel):
    signoff_code: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    applicant: str = ""
    amount: float = 0
    status: str = "draft"
    sign_date: str = ""
    case_id: int | None = None
    note: str = ""


class SignoffPatch(BaseModel):
    signoff_code: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    applicant: str | None = None
    amount: float | None = None
    status: str | None = None
    sign_date: str | None = None
    case_id: int | None = None
    note: str | None = None


class PurchaseIn(BaseModel):
    purchase_code: str = Field(min_length=1)
    item_name: str = Field(min_length=1)
    vendor_name: str = ""
    quantity: float = 0
    amount: float = 0
    status: str = "pending"
    case_id: int | None = None
    note: str = ""


class PurchasePatch(BaseModel):
    purchase_code: str | None = Field(default=None, min_length=1)
    item_name: str | None = Field(default=None, min_length=1)
    vendor_name: str | None = None
    quantity: float | None = None
    amount: float | None = None
    status: str | None = None
    case_id: int | None = None
    note: str | None = None


class ImportBatchIn(BaseModel):
    source_name: str = Field(min_length=1)
    status: str = "created"


class ImportRowsIn(BaseModel):
    rows: list[dict[str, Any]] = Field(min_length=1)


class ConfirmedImportField(BaseModel):
    row_number: int = Field(ge=1)
    target_table: str = Field(min_length=1)
    target_field: str = Field(min_length=1)


class ImportConfirmIn(BaseModel):
    dry_run: bool = True
    target_tables: list[str] = Field(default_factory=lambda: ["cases"], min_length=1)
    confirmed_fields: list[ConfirmedImportField] = Field(default_factory=list)
    accepted_warning_codes: list[str] = Field(default_factory=list)


class DevConsoleRunIn(BaseModel):
    command_id: str = Field(min_length=1)
    dry_run: bool = False


class LoginIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


AUTH_COOKIE_NAME = "ai_fee_user"
HANDLER_FORBIDDEN_PREFIXES = ("/api/audit-logs", "/api/import-batches", "/api/dev-console")  # 承辦不得使用（稽核/匯入/開發者控制台，含 demo-data）
LOCAL_AUTH_USERS: dict[str, dict[str, Any]] = {
    "ap01": {
        "username": "ap01",
        "role_code": "cio",
        "role_name": "CIO",
        "display_name": "CIO",
        # CIO 極簡：只給「決策總覽」，其他模組連卡片都不顯示（不是灰色，是隱藏）
        "default_module": "cio-overview",
        "allowed_modules": ["cio-overview"],
        "allowed_actions": ["read"],
    },
    "ap02": {
        "username": "ap02",
        "role_code": "manager_assistant",
        "role_name": "主管/助理",
        "display_name": "主管/助理",
        "default_module": "cases-module",
        "allowed_modules": [
            "budget",
            "projects",
            "signoff",
            "cases-module",
            "data-review",
            "contracts-module",
            "purchases",
            "payments-module",
        ],
        "allowed_actions": ["read", "edit", "import_preview", "preflight"],
    },
    "ap03": {
        "username": "ap03",
        "role_code": "handler",
        "role_name": "承辦",
        "display_name": "承辦",
        "default_module": "cases-module",
        "allowed_modules": ["projects", "cases-module", "purchases", "payments-module", "data-review"],
        "allowed_actions": ["read", "edit"],
    },
    # 第二位助理：雙人複核需要「另一位」助理來核，助理自己建的案件不能自己核
    "ap04": {
        "username": "ap04",
        "role_code": "manager_assistant",
        "role_name": "助理B",
        "display_name": "助理B",
        "default_module": "cases-module",
        "allowed_modules": [
            "budget",
            "projects",
            "signoff",
            "cases-module",
            "data-review",
            "contracts-module",
            "purchases",
            "payments-module",
        ],
        "allowed_actions": ["read", "edit", "import_preview", "preflight"],
    },
}


SESSION_SECRET = os.getenv("SESSION_SECRET") or secrets.token_hex(32)
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE_SECONDS", "28800"))  # 預設 8 小時後過期


def _sign_session(username: str) -> str:
    payload = f"{username}.{int(time.time())}"
    sig = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify_session(token: str) -> str | None:
    """驗證簽章 session cookie。回傳可信任的 username，否則 None。
    只認得本服務簽出來、且未過期的 token；偽造或過期一律拒絕。"""
    parts = (token or "").rsplit(".", 2)
    if len(parts) != 3:
        return None
    username, ts, sig = parts
    expected = hmac.new(SESSION_SECRET.encode(), f"{username}.{ts}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected) or username not in LOCAL_AUTH_USERS:
        return None
    try:
        age = time.time() - int(ts)
    except ValueError:
        return None
    if age < 0 or age > SESSION_MAX_AGE:
        return None
    return username


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 200_000)
    return hmac.compare_digest(dk.hex(), hash_hex)


def _load_user_password_hashes() -> dict[str, str]:
    """每個帳號密碼由環境變數 {USERNAME}_PASSWORD 提供（例：AP01_PASSWORD），
    啟動時各自加鹽雜湊存記憶體。未設定者無法登入。密碼絕不進原始碼。"""
    hashes: dict[str, str] = {}
    for username in LOCAL_AUTH_USERS:
        pw = os.getenv(f"{username.upper()}_PASSWORD", "")
        if pw:
            hashes[username] = _hash_password(pw)
    return hashes


USER_PASSWORD_HASHES = _load_user_password_hashes()


def ok(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def auth_user_payload(username: str) -> dict[str, Any]:
    user = LOCAL_AUTH_USERS.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="登入狀態已失效，請重新登入。")
    return dict(user)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


async def bind_actor(request: Request) -> None:
    """把已驗證的登入者綁到本請求（async 依賴，確保 contextvar 傳到同步端點）。"""
    username = _verify_session(request.cookies.get(AUTH_COOKIE_NAME, ""))
    set_current_actor(username or "anonymous")
    role = LOCAL_AUTH_USERS.get(username or "", {}).get("role_code")
    set_owner_scope(username if role == "handler" else None)


def create_app() -> FastAPI:
    settings = get_settings()
    web_dir = Path(__file__).resolve().parent / "web"
    app = FastAPI(
        title="Fee Contract Control",
        version="0.2.0-fresh",
        description="Fresh implementation for fee, contract, payment, document, and case tracking.",
        lifespan=lifespan,
        dependencies=[Depends(bind_actor)],
    )
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.middleware("http")
    async def _auth_gate(request: Request, call_next):
        # 所有 /api/* 都要登入，例外只有 /api/auth/*（登入/登出/查身分）。
        path = request.url.path
        if path.startswith("/api/") and not path.startswith("/api/auth/"):
            username = _verify_session(request.cookies.get(AUTH_COOKIE_NAME, ""))
            if not username:
                return JSONResponse({"detail": "請先登入。"}, status_code=401)
            user = LOCAL_AUTH_USERS[username]
            if user["role_code"] == "handler" and any(path.startswith(p) for p in HANDLER_FORBIDDEN_PREFIXES):
                return JSONResponse({"detail": "權限不足：承辦無權使用此功能。"}, status_code=403)
            if request.method in ("POST", "PATCH", "PUT", "DELETE"):
                if "edit" not in user["allowed_actions"]:
                    return JSONResponse({"detail": "權限不足：此帳號僅供檢視。"}, status_code=403)
        return await call_next(request)

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    @app.get("/dev-console", include_in_schema=False)
    def dev_console_home() -> FileResponse:
        return FileResponse(web_dir / "dev-console.html")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "service": settings.app_name,
            "version": "0.2.0-fresh",
            "database": {"type": "sqlite", "path": settings.database_path},
        }

    @app.post("/api/auth/login")
    def login(payload: LoginIn, response: Response) -> dict[str, Any]:
        username = payload.username.strip().lower()
        stored = USER_PASSWORD_HASHES.get(username)
        if not stored or not _verify_password(payload.password, stored):
            raise HTTPException(status_code=401, detail="帳號或密碼錯誤。")
        response.set_cookie(
            AUTH_COOKIE_NAME,
            _sign_session(username),
            httponly=True,
            samesite="lax",
        )
        return ok(auth_user_payload(username))

    @app.get("/api/auth/me")
    def current_user(request: Request) -> dict[str, Any]:
        username = _verify_session(request.cookies.get(AUTH_COOKIE_NAME, ""))
        if not username:
            raise HTTPException(status_code=401, detail="登入狀態已失效，請重新登入。")
        return ok(auth_user_payload(username))

    @app.post("/api/auth/logout")
    def logout(response: Response) -> dict[str, Any]:
        response.delete_cookie(AUTH_COOKIE_NAME)
        return ok({"logged_out": True})

    @app.get("/api/dashboard")
    def dashboard() -> dict[str, Any]:
        return ok(dashboard_summary())

    @app.get("/api/reports/monthly-spending")
    def monthly_spending() -> dict[str, Any]:
        return ok(monthly_spending_summary())

    @app.get("/api/todo")
    def todo_cases() -> dict[str, Any]:
        return ok(cases_needing_attention())

    @app.get("/api/reports/expiring-contracts")
    def expiring() -> dict[str, Any]:
        return ok(expiring_contracts())

    @app.get("/api/reports/cio-overview")
    def cio_overview_report() -> dict[str, Any]:
        return ok(cio_overview())

    @app.get("/api/dev-console/status")
    def dev_console_status() -> dict[str, Any]:
        return ok(console_status())

    @app.post("/api/dev-console/run")
    def dev_console_run(payload: DevConsoleRunIn) -> dict[str, Any]:
        try:
            return ok(run_console_command(payload.command_id, payload.dry_run))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown control panel command.") from exc
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(status_code=504, detail=f"Command timed out after {exc.timeout} seconds.") from exc

    # 測試種子資料（demo）：掛在 /api/dev-console 底下 → 承辦被既有前綴擋、CIO 唯讀擋，只有主管/助理可用。
    @app.get("/api/dev-console/demo-data/status")
    def demo_data_status() -> dict[str, Any]:
        return ok(demo_counts())

    @app.post("/api/dev-console/demo-data/load")
    def demo_data_load() -> dict[str, Any]:
        return ok(load_demo_data())

    @app.post("/api/dev-console/demo-data/clear")
    def demo_data_clear() -> dict[str, Any]:
        return ok(clear_demo_data())

    @app.get("/api/audit-logs")
    def audit_logs(
        limit: int = Query(100, ge=1, le=500),
        table_name: str | None = None,
        row_id: int | None = None,
        action: str | None = None,
    ) -> dict[str, Any]:
        return ok(
            list_audit_logs(
                limit=limit,
                table_name=table_name,
                row_id=row_id,
                action=action,
            )
        )

    @app.post("/api/import-batches", status_code=201)
    def create_import_batch_endpoint(payload: ImportBatchIn) -> dict[str, Any]:
        try:
            return ok(create_import_batch(payload.source_name, payload.status))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/import-batches")
    def import_batches(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_import_batches(limit))

    @app.get("/api/import-batches/{batch_id}")
    def import_batch(batch_id: int) -> dict[str, Any]:
        try:
            return ok(get_import_batch(batch_id))
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/import-batches/{batch_id}/rows", status_code=201)
    def stage_import_batch_rows(batch_id: int, payload: ImportRowsIn) -> dict[str, Any]:
        try:
            return ok(stage_import_rows(batch_id, payload.rows))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/import-batches/{batch_id}/rows")
    def import_batch_rows(
        batch_id: int,
        limit: int = Query(500, ge=1, le=500),
    ) -> dict[str, Any]:
        try:
            return ok(list_import_rows(batch_id, limit))
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/import-batches/{batch_id}/mapping-preview")
    def import_batch_mapping_preview(batch_id: int) -> dict[str, Any]:
        try:
            return ok(preview_import_mapping(batch_id))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/import-batches/{batch_id}/confirm-preflight")
    def preflight_import_confirm(batch_id: int, payload: ImportConfirmIn) -> dict[str, Any]:
        if payload.target_tables != ["cases"]:
            raise HTTPException(status_code=400, detail='Only target_tables=["cases"] is supported.')
        try:
            return ok(
                preflight_import_batch_confirm(
                    batch_id,
                    [field.model_dump() for field in payload.confirmed_fields],
                    payload.accepted_warning_codes,
                )
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/import-batches/{batch_id}/confirm")
    def confirm_import_batch(batch_id: int, payload: ImportConfirmIn) -> dict[str, Any]:
        if payload.dry_run is not True:
            raise HTTPException(status_code=400, detail="Only dry_run=true is supported.")
        if payload.target_tables != ["cases"]:
            raise HTTPException(status_code=400, detail='Only target_tables=["cases"] is supported.')
        try:
            return ok(
                confirm_import_batch_cases_dry_run(
                    batch_id,
                    [field.model_dump() for field in payload.confirmed_fields],
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/import-mapping-draft")
    def import_mapping_draft() -> dict[str, Any]:
        return ok(mapping_draft_catalog())

    @app.post("/api/cases", status_code=201)
    def create_case(payload: CaseIn) -> dict[str, Any]:
        if payload.status == "approved":
            raise HTTPException(status_code=422, detail="案件需經雙人複核核准，不能直接建立為『已核准』。")
        return handle_create("cases", payload.model_dump())

    @app.get("/api/cases")
    def cases(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("cases", limit))

    @app.get("/api/cases.csv", include_in_schema=False)
    def export_cases_csv() -> Response:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["案件編號", "案件名稱", "狀態", "金額", "負責人", "風險", "備註", "下一步"])
        for r in list_rows("cases", 500):
            writer.writerow([
                r.get("case_code", ""), r.get("title", ""), r.get("status", ""),
                r.get("amount", 0), r.get("owner", ""), r.get("risk_level", ""),
                r.get("note", ""), r.get("next_step", ""),
            ])
        return Response(
            content="﻿" + buf.getvalue(),  # BOM 讓 Excel 正確辨識 UTF-8
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=cases.csv"},
        )

    @app.patch("/api/cases/{case_id}")
    def update_case(case_id: int, payload: CasePatch) -> dict[str, Any]:
        if payload.status == "approved":
            raise HTTPException(status_code=422, detail="案件需經雙人複核核准，不能直接改為『已核准』。")
        return handle_change("cases", case_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/cases/{case_id}/submit")
    def submit_case_endpoint(case_id: int) -> dict[str, Any]:
        try:
            return ok(submit_case(case_id))
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/cases/{case_id}/approve")
    def approve_case_endpoint(case_id: int, request: Request) -> dict[str, Any]:
        approver = _verify_session(request.cookies.get(AUTH_COOKIE_NAME, "")) or ""
        if LOCAL_AUTH_USERS.get(approver, {}).get("role_code") != "manager_assistant":
            raise HTTPException(status_code=403, detail="只有助理/主管能複核核准案件。")
        try:
            return ok(approve_case(case_id, approver))
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/cases/{case_id}/disable")
    def disable_case(case_id: int) -> dict[str, Any]:
        return handle_disable("cases", case_id)

    @app.delete("/api/cases/{case_id}", status_code=204)
    def delete_case(case_id: int) -> None:
        handle_delete("cases", case_id)

    @app.get("/api/cases/{case_id}/360")
    def case_detail(case_id: int) -> dict[str, Any]:
        try:
            return ok(case_360(case_id))
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/api/contracts", status_code=201)
    def create_contract(payload: ContractIn) -> dict[str, Any]:
        return handle_create("contracts", payload.model_dump())

    @app.get("/api/contracts")
    def contracts(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("contracts", limit))

    @app.patch("/api/contracts/{contract_id}")
    def update_contract(contract_id: int, payload: ContractPatch) -> dict[str, Any]:
        return handle_change("contracts", contract_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/contracts/{contract_id}/disable")
    def disable_contract(contract_id: int) -> dict[str, Any]:
        return handle_disable("contracts", contract_id)

    @app.delete("/api/contracts/{contract_id}", status_code=204)
    def delete_contract(contract_id: int) -> None:
        handle_delete("contracts", contract_id)

    @app.post("/api/payments", status_code=201)
    def create_payment(payload: PaymentIn) -> dict[str, Any]:
        return handle_create("payments", payload.model_dump())

    @app.get("/api/payments")
    def payments(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("payments", limit))

    @app.patch("/api/payments/{payment_id}")
    def update_payment(payment_id: int, payload: PaymentPatch) -> dict[str, Any]:
        return handle_change("payments", payment_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/payments/{payment_id}/disable")
    def disable_payment(payment_id: int) -> dict[str, Any]:
        return handle_disable("payments", payment_id)

    @app.delete("/api/payments/{payment_id}", status_code=204)
    def delete_payment(payment_id: int) -> None:
        handle_delete("payments", payment_id)

    @app.post("/api/documents", status_code=201)
    def create_document(payload: DocumentIn) -> dict[str, Any]:
        return handle_create("documents", payload.model_dump())

    @app.get("/api/documents")
    def documents(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("documents", limit))

    @app.patch("/api/documents/{document_id}")
    def update_document(document_id: int, payload: DocumentPatch) -> dict[str, Any]:
        return handle_change("documents", document_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/documents/{document_id}/disable")
    def disable_document(document_id: int) -> dict[str, Any]:
        return handle_disable("documents", document_id)

    @app.delete("/api/documents/{document_id}", status_code=204)
    def delete_document(document_id: int) -> None:
        handle_delete("documents", document_id)

    # ---- 預算 budgets ----
    @app.post("/api/budgets", status_code=201)
    def create_budget(payload: BudgetIn) -> dict[str, Any]:
        return handle_create("budgets", payload.model_dump())

    @app.get("/api/budgets")
    def budgets(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("budgets", limit))

    @app.patch("/api/budgets/{budget_id}")
    def update_budget(budget_id: int, payload: BudgetPatch) -> dict[str, Any]:
        return handle_change("budgets", budget_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/budgets/{budget_id}/disable")
    def disable_budget(budget_id: int) -> dict[str, Any]:
        return handle_disable("budgets", budget_id)

    @app.delete("/api/budgets/{budget_id}", status_code=204)
    def delete_budget(budget_id: int) -> None:
        handle_delete("budgets", budget_id)

    # ---- 專案 projects ----
    @app.post("/api/projects", status_code=201)
    def create_project(payload: ProjectIn) -> dict[str, Any]:
        return handle_create("projects", payload.model_dump())

    @app.get("/api/projects")
    def projects(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("projects", limit))

    @app.patch("/api/projects/{project_id}")
    def update_project(project_id: int, payload: ProjectPatch) -> dict[str, Any]:
        return handle_change("projects", project_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/projects/{project_id}/disable")
    def disable_project(project_id: int) -> dict[str, Any]:
        return handle_disable("projects", project_id)

    @app.delete("/api/projects/{project_id}", status_code=204)
    def delete_project(project_id: int) -> None:
        handle_delete("projects", project_id)

    # ---- 簽呈 signoffs ----
    @app.post("/api/signoffs", status_code=201)
    def create_signoff(payload: SignoffIn) -> dict[str, Any]:
        return handle_create("signoffs", payload.model_dump())

    @app.get("/api/signoffs")
    def signoffs(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("signoffs", limit))

    @app.patch("/api/signoffs/{signoff_id}")
    def update_signoff(signoff_id: int, payload: SignoffPatch) -> dict[str, Any]:
        return handle_change("signoffs", signoff_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/signoffs/{signoff_id}/disable")
    def disable_signoff(signoff_id: int) -> dict[str, Any]:
        return handle_disable("signoffs", signoff_id)

    @app.delete("/api/signoffs/{signoff_id}", status_code=204)
    def delete_signoff(signoff_id: int) -> None:
        handle_delete("signoffs", signoff_id)

    # ---- 請購 purchases ----
    @app.post("/api/purchases", status_code=201)
    def create_purchase(payload: PurchaseIn) -> dict[str, Any]:
        return handle_create("purchases", payload.model_dump())

    @app.get("/api/purchases")
    def purchases(limit: int = Query(100, ge=1, le=500)) -> dict[str, Any]:
        return ok(list_rows("purchases", limit))

    @app.patch("/api/purchases/{purchase_id}")
    def update_purchase(purchase_id: int, payload: PurchasePatch) -> dict[str, Any]:
        return handle_change("purchases", purchase_id, payload.model_dump(exclude_unset=True))

    @app.post("/api/purchases/{purchase_id}/disable")
    def disable_purchase(purchase_id: int) -> dict[str, Any]:
        return handle_disable("purchases", purchase_id)

    @app.delete("/api/purchases/{purchase_id}", status_code=204)
    def delete_purchase(purchase_id: int) -> None:
        handle_delete("purchases", purchase_id)

    @app.get("/api/search")
    def search(q: str = Query(min_length=1)) -> dict[str, Any]:
        return ok(search_records(q))

    @app.get("/api/cmdb")
    def cmdb_placeholder() -> dict[str, Any]:
        return ok(
            {
                "status": "reserved",
                "reserved_fields": ["cmdb_ci_id", "service_owner", "asset_tag"],
                "next_step": "Connect to enterprise CMDB API after credentials and schema are approved.",
            }
        )

    return app


def handle_create(table: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return ok(insert_row(table, payload))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def handle_change(table: str, row_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        return ok(update_row(table, row_id, payload))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def handle_disable(table: str, row_id: int) -> dict[str, Any]:
    try:
        return ok(disable_row(table, row_id))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def handle_delete(table: str, row_id: int) -> None:
    try:
        delete_row(table, row_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


app = create_app()
