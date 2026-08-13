"""合約盤點表匯入（黃助理 2026-08-13 給的「合約盤點_主機組.xlsx」）。

用合成檔測核心規則，不依賴那份真檔（它含公司內部資料、不進版控）；
真檔存在時另外跑一個煙霧測試。
"""
import io
import os
from pathlib import Path

import openpyxl
import pytest
from fastapi.testclient import TestClient

REAL = Path(__file__).resolve().parents[1] / "docs" / "確認說明書" / "回饋0813" / "合約盤點_主機組.xlsx"

HEADERS = ["詩芸備註", "已確認完成", "合約編號", "合約名稱", "合約系統之內容說明",
           "合約狀態", "合約狀態詳細說明", "組別", "合約維護人", "廠商名稱",
           "廠商統編或ID", "合約開始日", "合約到期日"]


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "cinv.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _book(rows: list[list], lead_in: int = 7) -> bytes:
    """造一份跟真檔同構的盤點表：表頭前面有幾列填寫說明。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "主機組"
    for i in range(lead_in):
        ws.append([f"填寫說明第 {i + 1} 行"])
    ws.append(HEADERS)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _row(code, name, **kw):
    return [kw.get("note", ""), kw.get("confirmed", "True"), code, name,
            kw.get("content", ""), kw.get("status", "進行中"), kw.get("detail", ""),
            kw.get("group", "主機組"), kw.get("owner", "林宏喜"),
            kw.get("vendor", "神坊資訊股份有限公司"), kw.get("tax", "70461075"),
            kw.get("start", "2024-01-01"), kw.get("end", "2026-12-31")]


def test_表頭不在第一列也找得到(tmp_path):
    """各組交回來的檔案，說明列數可能不一樣，寫死列號第二個組就爆。"""
    from app.store import parse_contract_inventory_xlsx

    for lead in (0, 7, 15):
        res = parse_contract_inventory_xlsx(_book([_row("EF-1", "維護約")], lead_in=lead))
        assert res["count"] == 1 and res["contracts"][0]["contract_name"] == "維護約"


def test_AS400歸主機組(tmp_path):
    """使用者 2026-08-13 裁決：H 欄的 AS400 是系統名不是組別，歸主機組。"""
    from app.store import parse_contract_inventory_xlsx

    res = parse_contract_inventory_xlsx(_book([_row("EF-1", "約", group="AS400")]))
    assert res["contracts"][0]["group_name"] == "主機組"


def test_從說明文字抓出合約關聯(tmp_path):
    from app.store import parse_contract_inventory_xlsx

    rows = [
        _row("EF-20190726-046", "舊約", detail="舊維護合約，已由新合約取代EF-20240416-005"),
        _row("EF-20220629-012", "費調", detail="費用調整合約，會整併至EF-20240416-005"),
        _row("EF-20240416-005", "新約"),
    ]
    got = {c["external_code"]: c for c in parse_contract_inventory_xlsx(_book(rows))["contracts"]}
    assert got["EF-20190726-046"]["relation_hint"] == "renew"
    assert got["EF-20190726-046"]["related_codes"] == ["EF-20240416-005"]
    assert got["EF-20220629-012"]["relation_hint"] == "merge"
    assert got["EF-20240416-005"]["related_codes"] == []      # 沒提到別人就是沒關聯


def test_抓出原維護人供交接用(tmp_path):
    from app.store import parse_contract_inventory_xlsx

    res = parse_contract_inventory_xlsx(_book([
        _row("EF-1", "約", note="原合約維護人：張根榮", owner="黃紹育")]))
    c = res["contracts"][0]
    assert c["previous_owner"] == "張根榮" and c["owner"] == "黃紹育"


def test_匯入寫進合約主檔並保留盤點原文(tmp_path):
    """「查無後續合約」是盤點當下的標記，不是合約本身的狀態，硬套成系統狀態會失真，
    所以原文留在備註裡。"""
    with _client(tmp_path) as client:
        book = _book([_row("EF-20190726-046", "電子郵件服務租用契約書",
                           status="查無後續合約", content="維護二台IBM Power 720",
                           note="服務部移轉", detail="舊維護合約，已由新合約取代EF-1")])
        r = client.post("/api/contracts/import-xlsx?commit=true", content=book).json()["data"]
        assert r["created_count"] == 1

        k = client.get("/api/contracts").json()["data"][0]
        assert k["external_code"] == "EF-20190726-046"        # 公司的號照原樣留（含連字號）
        assert k["system_code"].startswith("CT")              # 系統自己的識別碼另外配
        assert k["vendor_tax_id"] == "70461075" and k["owner"] == "林宏喜"
        assert k["group_name"] == "主機組"
        assert k["progress_note"] == "舊維護合約，已由新合約取代EF-1"
        for keep in ("查無後續合約", "IBM Power 720", "服務部移轉"):
            assert keep in k["note"]                          # 盤點原文不丟


def test_重匯同一份不會長出第二套(tmp_path):
    """助理 8/19 盤點完會再給一次，同編號要更新不是新增。"""
    with _client(tmp_path) as client:
        book = _book([_row("EF-1", "原名稱", owner="林宏喜")])
        client.post("/api/contracts/import-xlsx?commit=true", content=book)

        book2 = _book([_row("EF-1", "更新後名稱", owner="鄭一鳴")])
        r = client.post("/api/contracts/import-xlsx?commit=true", content=book2).json()["data"]
        assert r["created_count"] == 0 and r["updated_count"] == 1

        rows = client.get("/api/contracts").json()["data"]
        assert len(rows) == 1
        assert rows[0]["contract_name"] == "更新後名稱" and rows[0]["owner"] == "鄭一鳴"


def test_關聯在第二輪才接才找得到後面的合約(tmp_path):
    with _client(tmp_path) as client:
        # 舊約排在前面、被指向的新約排在後面：先接會找不到
        book = _book([
            _row("EF-20190726-046", "舊約", detail="舊維護合約，已由新合約取代EF-20240416-005"),
            _row("EF-20240416-005", "新約"),
        ])
        r = client.post("/api/contracts/import-xlsx?commit=true", content=book).json()["data"]
        assert r["linked_count"] == 1

        by_code = {k["external_code"]: k for k in client.get("/api/contracts").json()["data"]}
        assert by_code["EF-20190726-046"]["parent_contract_id"] == by_code["EF-20240416-005"]["id"]
        assert by_code["EF-20190726-046"]["relation_type"] == "renew"


def test_預覽不寫入且回報要注意的事(tmp_path):
    with _client(tmp_path) as client:
        book = _book([
            _row("EF-20240416-005", "約一", confirmed="False"),
            _row("EF-20220629-012", "約二", note="原合約維護人：張根榮",
                 detail="已由新合約取代EF-20240416-005"),
        ])
        r = client.post("/api/contracts/import-xlsx?commit=false", content=book).json()["data"]
        assert r["preview"] is True and r["count"] == 2
        assert r["unconfirmed"] == 1          # 還沒填 V 的
        assert r["handover_hints"] == 1       # 有原維護人的
        assert r["relation_hints"] == 1
        assert client.get("/api/contracts").json()["data"] == []   # 預覽不寫入


def test_沒有名稱的列略過並說明原因(tmp_path):
    with _client(tmp_path) as client:
        book = _book([_row("EF-1", ""), _row("EF-2", "正常的")])
        r = client.post("/api/contracts/import-xlsx?commit=true", content=book).json()["data"]
        assert r["created_count"] == 1 and r["skipped_count"] == 1
        assert "沒有合約名稱" in r["skipped"][0]["reason"]


def test_沒有合約編號的那筆重匯也不會撞號(tmp_path):
    """真檔裡有 1 筆沒填合約編號。識別鍵只看編號的話，它每次都被當新的，
    第二次匯入就撞 contract_code 的唯一鍵直接 500（實際踩到過）。"""
    with _client(tmp_path) as client:
        book = _book([_row("", "沒有編號的合約"), _row("EF-20240416-005", "正常的")])
        first = client.post("/api/contracts/import-xlsx?commit=true", content=book).json()["data"]
        assert first["created_count"] == 2

        second = client.post("/api/contracts/import-xlsx?commit=true", content=book)
        assert second.status_code == 200
        r = second.json()["data"]
        assert r["created_count"] == 0 and r["updated_count"] == 2
        assert len(client.get("/api/contracts").json()["data"]) == 2


def test_互相指向對方時不接關聯(tmp_path):
    """真實資料：「115年配合集團會啟動續約 (與EF-20240222-002一起追蹤)」兩邊互相提到對方。
    照接會繞成循環，續約鏈往上追追不完。"""
    with _client(tmp_path) as client:
        book = _book([
            _row("EF-20240222-002", "甲約", detail="已由新合約取代EF-20250805-008"),
            _row("EF-20250805-008", "乙約", detail="舊合約取代EF-20240222-002"),
        ])
        r = client.post("/api/contracts/import-xlsx?commit=true", content=book).json()["data"]
        assert r["linked_count"] == 1                    # 只接得起一邊
        assert any("循環" in s["reason"] for s in r["skipped"])

        rows = client.get("/api/contracts").json()["data"]
        linked = [k for k in rows if k["parent_contract_id"]]
        assert len(linked) == 1                          # 另一邊留白給人判斷


def test_一起追蹤不算從屬關係(tmp_path):
    from app.store import parse_contract_inventory_xlsx

    res = parse_contract_inventory_xlsx(_book([
        _row("EF-20250805-008", "約",
             detail="授權暨維護合約，115年配合集團會啟動續約 (與EF-20240222-002一起追蹤)")]))
    c = res["contracts"][0]
    assert c["related_codes"] == ["EF-20240222-002"]     # 有提到對方
    assert c["relation_hint"] == ""                      # 但那不是「續約自」


def test_承辦不可匯入合約(tmp_path):
    with _client(tmp_path, login="ap03") as client:
        assert client.post("/api/contracts/import-xlsx?commit=false",
                           content=_book([_row("EF-1", "約")])).status_code == 403


@pytest.mark.skipif(not REAL.exists(), reason="真實盤點表不存在（docs/ 不進版控）")
def test_真檔煙霧測試(tmp_path):
    from app.store import parse_contract_inventory_xlsx

    res = parse_contract_inventory_xlsx(REAL.read_bytes())
    assert res["count"] > 50
    assert "填寫說明與範例" in res["skipped_sheets"]         # 說明頁自動略過
    assert all(c["group_name"] != "AS400" for c in res["contracts"])
    assert any(c["previous_owner"] for c in res["contracts"])
