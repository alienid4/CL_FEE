"""人員名單匯入：一列一人，欄名認「姓名/部門/Email」定位，不寫死順序。
以姓名為識別鍵，同姓名更新（空欄不覆蓋既有值）、沒見過的新增，重匯安全。"""
import io
import os

import openpyxl
from fastapi.testclient import TestClient


def _client(tmp_path, login="admin"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "personnel_import.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _wb(rows, header=("姓名", "部門", "Email")):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(list(header))
    for r in rows:
        ws.append(list(r))
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def test_parse_extracts_name_group_email():
    from app.store import parse_personnel_xlsx

    data = _wb([("王小明", "主機組", "wang@co.com"), ("陳小華", "網路組", "chen@co.com")])
    records = parse_personnel_xlsx(data)
    assert len(records) == 2
    assert records[0] == {"name": "王小明", "group_name": "主機組", "email": "wang@co.com"}


def test_parse_recognizes_alternate_header_names():
    from app.store import parse_personnel_xlsx

    data = _wb([("李四", "資料庫組", "li@co.com")], header=("員工姓名", "組別", "信箱"))
    records = parse_personnel_xlsx(data)
    assert records == [{"name": "李四", "group_name": "資料庫組", "email": "li@co.com"}]


def test_parse_skips_blank_name_rows():
    from app.store import parse_personnel_xlsx

    data = _wb([("王小明", "主機組", "wang@co.com"), ("", "網路組", "x@co.com")])
    records = parse_personnel_xlsx(data)
    assert len(records) == 1


def test_parse_sheet_without_name_column_is_skipped():
    from app.store import parse_personnel_xlsx

    data = _wb([("2026", "說明")], header=("年度", "備註"))
    assert parse_personnel_xlsx(data) == []


def test_preview_then_commit_creates_and_updates(tmp_path):
    with _client(tmp_path) as client:
        data = _wb([("王小明", "主機組", "wang@co.com"), ("陳小華", "網路組", "")])
        r = client.post("/api/personnel-master/import-xlsx?commit=false", content=data)
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["count"] == 2 and d["missing_email"] == 1

        r2 = client.post("/api/personnel-master/import-xlsx?commit=true", content=data)
        d2 = r2.json()["data"]
        assert d2["created_count"] == 2 and d2["updated_count"] == 0

        people = client.get("/api/personnel-master").json()["data"]["masters"]
        wang = next(p for p in people if p["name"] == "王小明")
        assert wang["group_name"] == "主機組" and wang["email"] == "wang@co.com"


def test_reimport_updates_without_duplicating(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/personnel-master/import-xlsx?commit=true",
                     content=_wb([("王小明", "主機組", "old@co.com")]))
        client.post("/api/personnel-master/import-xlsx?commit=true",
                     content=_wb([("王小明", "網路組", "new@co.com")]))
        people = client.get("/api/personnel-master").json()["data"]["masters"]
        matches = [p for p in people if p["name"] == "王小明"]
        assert len(matches) == 1  # 沒有長出重複
        assert matches[0]["group_name"] == "網路組" and matches[0]["email"] == "new@co.com"


def test_blank_columns_do_not_overwrite_existing_values(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/personnel-master/import-xlsx?commit=true",
                     content=_wb([("王小明", "主機組", "wang@co.com")]))
        # 重匯一份只有姓名、部門/Email 空白的檔——不該把已填的值洗掉
        client.post("/api/personnel-master/import-xlsx?commit=true",
                     content=_wb([("王小明", "", "")]))
        people = client.get("/api/personnel-master").json()["data"]["masters"]
        wang = next(p for p in people if p["name"] == "王小明")
        assert wang["group_name"] == "主機組" and wang["email"] == "wang@co.com"


def test_non_manager_cannot_import(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        r = client.post("/api/personnel-master/import-xlsx?commit=true",
                         content=_wb([("王小明", "主機組", "wang@co.com")]))
        assert r.status_code == 403


def test_empty_upload_rejected(tmp_path):
    with _client(tmp_path) as client:
        r = client.post("/api/personnel-master/import-xlsx?commit=false", content=b"")
        assert r.status_code == 400
