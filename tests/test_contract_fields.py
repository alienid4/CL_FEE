"""合約主檔欄位規格（黃助理 2026-08-03 附件一）：
系統識別碼與增購子號、統編格式、到期警示四色、黃紅燈必填進度說明、增購只能掛同案既有合約。"""
import os
from datetime import date, timedelta

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "contract.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _case(client, title="合約測試案"):
    return client.post("/api/cases", json={"title": title}).json()["data"]


def _contract(client, **kw):
    body = {"contract_code": "K1", "contract_name": "維護約", "start_date": "2026-01-01", **kw}
    return client.post("/api/contracts", json=body)


def test_系統識別碼依合約起日發號且純英數(tmp_path):
    with _client(tmp_path) as client:
        from app.store import is_system_code_valid

        a = _contract(client, contract_code="K1").json()["data"]
        b = _contract(client, contract_code="K2").json()["data"]
        assert a["system_code"] == "CT20260001" and b["system_code"] == "CT20260002"
        assert all(is_system_code_valid(c["system_code"]) for c in (a, b))
        # 年份看合約起日，不是建檔當天——補建舊約才不會掛到今年
        old = _contract(client, contract_code="K3", start_date="2024-05-01").json()["data"]
        assert old["system_code"] == "CT20240001"


def test_增購掛在原合約底下用子號(tmp_path):
    with _client(tmp_path) as client:
        c = _case(client)
        main = _contract(client, contract_code="M1", case_id=c["id"]).json()["data"]
        addon = _contract(client, contract_code="M1A", case_id=c["id"],
                          relation_type="addon", parent_contract_id=main["id"]).json()["data"]
        assert addon["system_code"] == main["system_code"] + "A01"
        addon2 = _contract(client, contract_code="M1B", case_id=c["id"],
                           relation_type="addon", parent_contract_id=main["id"]).json()["data"]
        assert addon2["system_code"] == main["system_code"] + "A02"   # 不覆蓋，往後掛


def test_增購必須指定原合約且限同案(tmp_path):
    with _client(tmp_path) as client:
        c1, c2 = _case(client, "案一"), _case(client, "案二")
        m1 = _contract(client, contract_code="A1", case_id=c1["id"]).json()["data"]

        r = _contract(client, contract_code="A2", case_id=c1["id"], relation_type="addon")
        assert r.status_code == 422 and "原合約" in r.json()["detail"]

        r2 = _contract(client, contract_code="A3", case_id=c2["id"],
                       relation_type="addon", parent_contract_id=m1["id"])
        assert r2.status_code == 422 and "同一個案件" in r2.json()["detail"]


def test_增購開放條件依同案既有合約數(tmp_path):
    with _client(tmp_path) as client:
        c = _case(client)
        opt = client.get(f"/api/cases/{c['id']}/addon-options").json()["data"]
        assert opt["mode"] == "disabled" and "尚無既有合約" in opt["hint"]

        m1 = _contract(client, contract_code="B1", case_id=c["id"]).json()["data"]
        opt = client.get(f"/api/cases/{c['id']}/addon-options").json()["data"]
        assert opt["mode"] == "auto" and opt["contracts"][0]["id"] == m1["id"]

        _contract(client, contract_code="B2", case_id=c["id"])
        opt = client.get(f"/api/cases/{c['id']}/addon-options").json()["data"]
        assert opt["mode"] == "choose" and opt["count"] == 2


def test_統一編號要八碼數字(tmp_path):
    with _client(tmp_path) as client:
        assert _contract(client, contract_code="T1", vendor_tax_id="1234").status_code == 422
        assert _contract(client, contract_code="T2", vendor_tax_id="1234567A").status_code == 422
        ok = _contract(client, contract_code="T3", vendor_tax_id="12345678")
        assert ok.status_code == 201 and ok.json()["data"]["vendor_tax_id"] == "12345678"


def test_到期警示四色(tmp_path):
    with _client(tmp_path) as client:
        today = date.today()
        far = _contract(client, contract_code="L1", end_date=str(today + timedelta(days=200))).json()["data"]
        near = _contract(client, contract_code="L2", end_date=str(today + timedelta(days=30)),
                         progress_note="續約評估中").json()["data"]
        over = _contract(client, contract_code="L3", end_date=str(today - timedelta(days=1)),
                         progress_note="已不續約，等結案").json()["data"]
        none_ = _contract(client, contract_code="L4").json()["data"]
        merged = _contract(client, contract_code="L5", end_date=str(today - timedelta(days=5)),
                           end_reason="merged").json()["data"]

        lights = {c["contract_code"]: c["expiry_light"]
                  for c in client.get("/api/contracts").json()["data"]}
        assert lights["L1"] == "green" and lights["L2"] == "yellow" and lights["L3"] == "red"
        assert lights["L4"] == "none"      # 沒填到期日≠還早，不能混進綠燈
        assert lights["L5"] == "gray"      # 已整併：不再按日期催
        assert far and near and over and none_ and merged


def test_黃紅燈缺進度說明會被標記但不擋存檔(tmp_path):
    """助理規格是「黃燈且未填進度說明時，到期追蹤不得標示為完成」——要的是追蹤不能算結案，
    不是不准建檔。擋存檔會連帶擋掉匯入既有合約（那些一進來常常就是黃燈）。"""
    with _client(tmp_path) as client:
        today = date.today()
        r = _contract(client, contract_code="P1", end_date=str(today + timedelta(days=20)))
        assert r.status_code == 201                      # 存得進去

        filled = _contract(client, contract_code="P2", end_date=str(today + timedelta(days=20)),
                           progress_note="已送續約簽呈").json()["data"]
        flags = {k["contract_code"]: k["needs_progress_note"]
                 for k in client.get("/api/contracts").json()["data"]}
        assert flags["P1"] is True                       # 但會被標出來：追蹤還不能算完成
        assert flags["P2"] is False                      # 填了就不標

        # 改成不續約 → 轉灰燈，本來就不用再追到期，旗標跟著關掉
        client.patch(f"/api/contracts/{filled['id']}", json={"end_reason": "not_renew"})
        after = {k["contract_code"]: k["expiry_light"] for k in client.get("/api/contracts").json()["data"]}
        assert after["P2"] == "gray"


def test_合約可獨立記負責人組別機房與公司合約系統編號(tmp_path):
    with _client(tmp_path) as client:
        c = _contract(client, contract_code="F1", owner="王小明", group_name="主機組",
                      locations="板橋,內湖", external_code="HQ-2026-777").json()["data"]
        assert c["owner"] == "王小明" and c["group_name"] == "主機組"
        assert c["locations"] == "板橋,內湖"          # 可複選，逗號分隔
        # 公司內部合約系統編號是別人的號，照原樣留（不套系統編號的純英數規則）
        assert c["external_code"] == "HQ-2026-777"


def test_合約迄日不得早於起日(tmp_path):
    with _client(tmp_path) as client:
        r = _contract(client, contract_code="D1", start_date="2026-06-01", end_date="2026-05-01")
        assert r.status_code == 422 and "不能早於" in r.json()["detail"]


def test_既有合約補發識別碼且先主約後增購(tmp_path):
    with _client(tmp_path) as client:
        import app.store as store

        c = _case(client)
        main = _contract(client, contract_code="OLD1", case_id=c["id"]).json()["data"]
        addon = _contract(client, contract_code="OLD2", case_id=c["id"],
                          relation_type="addon", parent_contract_id=main["id"]).json()["data"]
        # 模擬 0803 之前建的舊資料：識別碼欄位是空的
        with store.connect() as conn:
            conn.execute("UPDATE contracts SET system_code = '', system_seq = 0")

        r = client.post("/api/dev-console/contract-codes/fix").json()["data"]
        assert r["filled"] == 2
        codes = {k["contract_code"]: k["system_code"] for k in client.get("/api/contracts").json()["data"]}
        assert codes["OLD1"].startswith("CT")
        assert codes["OLD2"] == codes["OLD1"] + "A01"      # 增購仍掛在原合約底下
        assert addon["id"] and main["id"]

        assert client.post("/api/dev-console/contract-codes/fix").json()["data"]["filled"] == 0  # 冪等


def test_舊資料庫重開就自動補識別碼(tmp_path):
    """system_code 是 0803 才加的欄位，之前建的合約全是空的，畫面上那一欄會整排空白。
    要人到後台按一次才有＝沒人知道要按，等於預設是壞的。改成開機自動補。"""
    with _client(tmp_path) as client:
        import app.store as store

        c = _case(client)
        main = _contract(client, contract_code="B4", case_id=c["id"]).json()["data"]
        _contract(client, contract_code="B4A", case_id=c["id"],
                  relation_type="addon", parent_contract_id=main["id"])
        with store.connect() as conn:                      # 退回成「舊資料庫」的樣子
            conn.execute("UPDATE contracts SET system_code = '', system_seq = 0")
        assert all(k["system_code"] == "" for k in client.get("/api/contracts").json()["data"])

    # 重開服務（等同使用者更新完按 service.bat 重啟）：不必進後台按任何東西
    with _client(tmp_path) as client2:
        codes = {k["contract_code"]: k["system_code"] for k in client2.get("/api/contracts").json()["data"]}
        assert codes["B4"].startswith("CT") and codes["B4A"] == codes["B4"] + "A01"


def test_核准簽核銷簽呈編號可選填且跟系統識別碼是兩回事(tmp_path):
    """第四輪回饋 AC-05：合約要能記「核准簽」「核銷簽」兩個簽呈編號，非必填、
    跟系統自動配發的 Contract ID（system_code）不是同一件事。"""
    with _client(tmp_path) as client:
        no_signoff = _contract(client, contract_code="S1").json()["data"]
        assert no_signoff["signoff_ref"] == "" and no_signoff["signoff_no"] == ""  # 非必填，留空存得進去

        c = _contract(client, contract_code="S2", signoff_ref="APR-2026-001", signoff_no="SETL-2026-088").json()["data"]
        assert c["signoff_ref"] == "APR-2026-001"
        assert c["signoff_no"] == "SETL-2026-088"
        assert c["signoff_ref"] != c["system_code"] and c["signoff_no"] != c["system_code"]

        updated = client.patch(f"/api/contracts/{c['id']}", json={"signoff_no": "SETL-2026-099"}).json()["data"]
        assert updated["signoff_no"] == "SETL-2026-099" and updated["signoff_ref"] == "APR-2026-001"


def test_對應專案由系統自動關聯(tmp_path):
    with _client(tmp_path) as client:
        c = _case(client, "有專案的案子")
        prj = client.post("/api/projects", json={"project_name": "機房搬遷", "case_id": c["id"]}).json()["data"]
        k = _contract(client, contract_code="J1", case_id=c["id"]).json()["data"]
        assert k["project_id"] == prj["id"]      # 使用者不用選，系統自己接起來
