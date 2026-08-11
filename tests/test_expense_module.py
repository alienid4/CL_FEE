"""費用模組三層（黃助理 0803 附件一）第一批：
第一層費用主檔（有合約帶入、總費用唯讀）＋第二層里程碑／定期費用的排程產生、檢核、預覽、確認、改版。"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "expense.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _contract(client, amount=1200000):
    return client.post("/api/contracts", json={
        "contract_code": "K1", "contract_name": "主機維護約", "vendor_name": "中華電信",
        "vendor_tax_id": "12345678", "amount": amount,
        "start_date": "2026-01-01", "end_date": "2026-12-31", "owner": "王小明",
    }).json()["data"]


def _master(client, **kw):
    body = {"modes": "milestone", "signoff_ref": "SG-001", **kw}
    return client.post("/api/expenses", json=body)


def test_有合約時欄位由合約帶入且總費用不得人工改(tmp_path):
    with _client(tmp_path) as client:
        k = _contract(client)
        # 故意送一個不一樣的金額：助理寫明總費用有合約時唯讀反灰，要以合約為準
        m = _master(client, contract_id=k["id"], total_amount=999).json()["data"]
        assert m["total_amount"] == 1200000
        assert m["vendor_name"] == "中華電信" and m["vendor_tax_id"] == "12345678"
        assert m["start_date"] == "2026-01-01" and m["end_date"] == "2026-12-31"
        assert m["expense_name"] == "主機維護約" and m["owner"] == "王小明"


def test_無合約時期間清空且總費用改人工填(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="例行性電費", total_amount=60000,
                    start_date="2026-01-01", end_date="2026-12-31").json()["data"]
        assert m["total_amount"] == 60000
        assert m["start_date"] == "" and m["end_date"] == ""   # 助理：無合約時停用、不得輸入


def test_總費用與模式與簽呈編號的必填檢核(tmp_path):
    with _client(tmp_path) as client:
        assert _master(client, expense_name="沒金額").status_code == 422
        assert _master(client, expense_name="零元", total_amount=0).status_code == 422
        assert _master(client, expense_name="沒模式", total_amount=100, modes="").status_code == 422
        no_sign = client.post("/api/expenses", json={
            "expense_name": "沒簽呈", "total_amount": 100, "modes": "periodic"})
        assert no_sign.status_code == 422 and "無編號原因" in no_sign.json()["detail"]
        # 沒編號但寫了原因 → 放行
        assert client.post("/api/expenses", json={
            "expense_name": "沒簽呈但有原因", "total_amount": 100, "modes": "periodic",
            "signoff_none_reason": "小額零星採購免簽"}).status_code == 201


def test_里程碑依總期數產生可逐期編輯的明細(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="專案", total_amount=1000000).json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "milestone", "section_name": "軟體授權及專業服務費",
            "section_amount": 1000000, "price_method": "percent", "periods": 3,
        }).json()["data"]
        gen = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]
        assert len(gen["schedules"]) == 3
        assert [s["seq"] for s in gen["schedules"]] == [1, 2, 3]
        # 助理明確寫過：不得只存第一期後由系統推測其他期
        assert all(s["planned_amount"] == 0 and s["milestone_name"] == "" for s in gen["schedules"])
        assert gen["can_confirm"] is False        # 還沒填，當然不能確認


def test_里程碑比例與金額檢核講清楚差多少(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="專案", total_amount=1000000).json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "milestone", "section_amount": 1000000, "price_method": "percent", "periods": 2,
        }).json()["data"]
        rows = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"]
        client.patch(f"/api/expense-schedules/{rows[0]['id']}", json={
            "milestone_name": "簽約款", "percent": 30, "planned_amount": 300000})
        client.patch(f"/api/expense-schedules/{rows[1]['id']}", json={
            "milestone_name": "驗收款", "percent": 60, "planned_amount": 600000})

        pv = client.get(f"/api/expense-sections/{sec['id']}/preview").json()["data"]
        assert pv["can_confirm"] is False
        joined = "；".join(pv["problems"])
        assert "90" in joined and "100%" in joined          # 比例差 10%
        assert "差" in joined                                # 金額也差，且有講差多少

        client.patch(f"/api/expense-schedules/{rows[1]['id']}", json={
            "percent": 70, "planned_amount": 700000})
        pv2 = client.get(f"/api/expense-sections/{sec['id']}/preview").json()["data"]
        assert pv2["problems"] == [] and pv2["can_confirm"] is True


def test_自訂里程碑名稱要填備註(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="專案", total_amount=100).json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "milestone", "section_amount": 100, "price_method": "fixed", "periods": 1,
        }).json()["data"]
        row = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]["schedules"][0]
        client.patch(f"/api/expense-schedules/{row['id']}", json={
            "milestone_name": "自訂", "planned_amount": 100})
        pv = client.get(f"/api/expense-sections/{sec['id']}/preview").json()["data"]
        assert any("自訂里程碑備註" in p for p in pv["problems"])

        client.patch(f"/api/expense-schedules/{row['id']}", json={"custom_name": "尾款"})
        assert client.get(f"/api/expense-sections/{sec['id']}/preview").json()["data"]["can_confirm"] is True


def test_定期費用依頻率順延推算後續各期(tmp_path):
    """助理的實作例：每季、共 20 期、每期 200,000，自首期年月起每三個月一期。"""
    with _client(tmp_path) as client:
        m = _master(client, expense_name="維運服務費", total_amount=4000000,
                    modes="periodic").json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "periodic", "section_name": "維運服務費", "section_amount": 4000000,
            "frequency": "quarterly", "periods": 20, "first_amount": 200000,
            "first_month": "2026-01", "first_due_date": "2026-01-10",
        }).json()["data"]
        gen = client.post(f"/api/expense-sections/{sec['id']}/generate").json()["data"]
        rows = gen["schedules"]
        assert len(rows) == 20
        assert rows[0]["expense_month"] == "2026-01" and rows[1]["expense_month"] == "2026-04"
        assert rows[4]["expense_month"] == "2027-01"          # 跨年繼續順延
        assert rows[1]["due_date"] == "2026-04-10"            # 預計應付日一起順延
        assert all(r["planned_amount"] == 200000 for r in rows)
        assert gen["can_confirm"] is True                     # 20×20萬＝400萬，對得起來


def test_金額對不起來不准確認(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="維運", total_amount=1000, modes="periodic").json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "periodic", "section_amount": 1000, "frequency": "monthly",
            "periods": 3, "first_amount": 200, "first_month": "2026-01",
        }).json()["data"]
        client.post(f"/api/expense-sections/{sec['id']}/generate")
        r = client.post(f"/api/expense-sections/{sec['id']}/confirm")
        assert r.status_code == 422 and "差" in r.json()["detail"]   # 600 vs 1000


def test_確認排程記下確認人與時間(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="維運", total_amount=600, modes="periodic").json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "periodic", "section_amount": 600, "frequency": "monthly",
            "periods": 3, "first_amount": 200, "first_month": "2026-01",
        }).json()["data"]
        client.post(f"/api/expense-sections/{sec['id']}/generate")
        done = client.post(f"/api/expense-sections/{sec['id']}/confirm").json()["data"]
        assert done["status"] == "confirmed" and done["confirmed_by"] == "ap02" and done["confirmed_at"]

        # 已確認就不給直接重產排程（會把人工調過的值洗掉）
        again = client.post(f"/api/expense-sections/{sec['id']}/generate")
        assert again.status_code == 409


def test_重新編輯會建新版本並保留原版(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="維運", total_amount=600, modes="periodic").json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "periodic", "section_amount": 600, "frequency": "monthly",
            "periods": 3, "first_amount": 200, "first_month": "2026-01",
        }).json()["data"]
        client.post(f"/api/expense-sections/{sec['id']}/generate")
        client.post(f"/api/expense-sections/{sec['id']}/confirm")

        r = client.post(f"/api/expense-sections/{sec['id']}/reopen").json()["data"]
        assert r["section"]["status"] == "draft" and r["section"]["version"] == 2
        archived = r["archived_section_id"]
        # 原版整段留著（含明細），查得到當初確認的是什麼
        old = client.get(f"/api/expense-sections/{archived}/preview").json()["data"]
        assert old["section"]["status"] == "confirmed" and len(old["schedules"]) == 3


def test_混合型要各段加總等於總費用(tmp_path):
    with _client(tmp_path) as client:
        m = _master(client, expense_name="混合型", total_amount=1000,
                    modes="milestone,periodic").json()["data"]
        chk = client.get(f"/api/expenses/{m['id']}/check").json()["data"]
        assert chk["balanced"] is False and chk["missing_sections"] == ["里程碑", "定期費用"]

        client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "milestone", "section_amount": 400, "price_method": "fixed", "periods": 1})
        client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "periodic", "section_amount": 600, "frequency": "monthly",
            "periods": 3, "first_amount": 200, "first_month": "2026-01"})
        chk2 = client.get(f"/api/expenses/{m['id']}/check").json()["data"]
        assert chk2["balanced"] is True and chk2["diff"] == 0 and chk2["missing_sections"] == []


def test_最低承諾金額這批還沒開放(tmp_path):
    """A8 拍板分兩批：先做里程碑與定期費用，最低承諾金額排下一輪。
    先擋住並講清楚，不要讓人以為建好了卻產不出排程。"""
    with _client(tmp_path) as client:
        m = _master(client, expense_name="承諾", total_amount=100, modes="commitment").json()["data"]
        sec = client.post(f"/api/expenses/{m['id']}/sections", json={
            "mode": "commitment", "section_amount": 100, "periods": 3}).json()["data"]
        r = client.post(f"/api/expense-sections/{sec['id']}/generate")
        assert r.status_code == 422 and "最低承諾金額" in r.json()["detail"]
