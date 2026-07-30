"""角色層級：部長 → 組長 → 承辦，助理在中間協助（使用者說明 2026-07-30）。

重點是「組長也可能是承辦」——很多簽呈組長自己做。所以組長的可見範圍不是「只看自己的」，
而是「本組全部」（自己送的自然也在裡面）；核准權組長／部長／助理都有，唯一鐵則是
不能核准自己建立的案件，所以組長自己送的案由部長或助理來核。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "roles.db")
    from app.main import create_app

    return TestClient(create_app())


def _login(client, username):
    r = client.post("/api/auth/login", json={"username": username, "password": "T3st!Pass"})
    assert r.status_code == 200, r.text


def _seed(table, payload):
    from app import store

    return store.insert_row(table, payload)


def _codes(client):
    return {c["case_code"] for c in client.get("/api/cases").json()["data"]}


def test_組長看本組全部看不到別組(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "NET-1", "title": "本組甲的案", "owner": "ap03", "group_name": "網路組"})
        _seed("cases", {"case_code": "NET-2", "title": "本組乙的案", "owner": "someone", "group_name": "網路組"})
        _seed("cases", {"case_code": "DB-1", "title": "別組的案", "owner": "other", "group_name": "資料庫組"})
        _login(client, "ap05")                     # ap05＝網路組組長
        assert _codes(client) == {"NET-1", "NET-2"}


def test_部長看全部(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "NET-1", "title": "a", "group_name": "網路組"})
        _seed("cases", {"case_code": "DB-1", "title": "b", "group_name": "資料庫組"})
        _login(client, "ap06")
        assert _codes(client) == {"NET-1", "DB-1"}


def test_承辦仍只看自己的(tmp_path):
    with _client(tmp_path) as client:
        _seed("cases", {"case_code": "MINE", "title": "我的", "owner": "ap03", "group_name": "網路組"})
        _seed("cases", {"case_code": "SAME-GROUP", "title": "同組別人的", "owner": "ap09", "group_name": "網路組"})
        _login(client, "ap03")
        assert _codes(client) == {"MINE"}          # 同組別人的也看不到


def test_組長自己建的案會自動歸本組(tmp_path):
    """組長自己當承辦送案時，組別要自動帶本組，否則他建完自己看不到。"""
    with _client(tmp_path) as client:
        _login(client, "ap05")
        c = client.post("/api/cases", json={"title": "組長自己做的簽呈"}).json()["data"]
        assert c["group_name"] == "網路組"
        assert "組長自己做的簽呈" in {x["title"] for x in client.get("/api/cases").json()["data"]}


def test_組長不能核准自己送的案由部長來核(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap05")
        c = client.post("/api/cases", json={"title": "組長送的案"}).json()["data"]
        client.post(f"/api/cases/{c['id']}/submit")
        assert client.post(f"/api/cases/{c['id']}/approve").status_code == 403   # 自己不能核自己
        _login(client, "ap06")                                                  # 換部長
        r = client.post(f"/api/cases/{c['id']}/approve")
        assert r.status_code == 200, r.text
        assert r.json()["data"]["seq"] == 1                                      # 核准才配正式號


def test_助理也能核准組長送的案(tmp_path):
    """使用者拍板：助理維持現在就能核。"""
    with _client(tmp_path) as client:
        _login(client, "ap05")
        c = client.post("/api/cases", json={"title": "組長送的案"}).json()["data"]
        client.post(f"/api/cases/{c['id']}/submit")
        _login(client, "ap02")
        assert client.post(f"/api/cases/{c['id']}/approve").status_code == 200


def test_組長可以退件併案駁回(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap03")                     # 承辦送案
        c = client.post("/api/cases", json={"title": "承辦送的案"}).json()["data"]
        client.post(f"/api/cases/{c['id']}/submit")
        from app import store
        store.update_row("cases", c["id"], {"group_name": "網路組"})   # 歸到網路組
        _login(client, "ap05")                     # 組長審
        r = client.post(f"/api/cases/{c['id']}/return", json={"reason": "缺附件"})
        assert r.status_code == 200, r.text
        assert r.json()["data"]["status"] == "returned"


def test_承辦仍然不能做審核決定(tmp_path):
    with _client(tmp_path) as client:
        _login(client, "ap02")
        c = client.post("/api/cases", json={"title": "案"}).json()["data"]
        client.post(f"/api/cases/{c['id']}/submit")
        _login(client, "ap03")
        assert client.post(f"/api/cases/{c['id']}/approve").status_code == 403
        assert client.post(f"/api/cases/{c['id']}/return", json={"reason": "x"}).status_code == 403
        assert client.post(f"/api/cases/{c['id']}/reject", json={"reason": "x"}).status_code == 403


def test_組長看得到本組案件底下的合約與付款(tmp_path):
    """合約/付款靠 case_id 掛在案件上，組別隔離要一路蓋到下層。"""
    with _client(tmp_path) as client:
        mine = _seed("cases", {"case_code": "NET-C", "title": "本組", "group_name": "網路組"})
        theirs = _seed("cases", {"case_code": "DB-C", "title": "別組", "group_name": "資料庫組"})
        _seed("contracts", {"contract_code": "K-NET", "contract_name": "本組約", "case_id": mine["id"]})
        _seed("contracts", {"contract_code": "K-DB", "contract_name": "別組約", "case_id": theirs["id"]})
        _login(client, "ap05")
        codes = {k["contract_code"] for k in client.get("/api/contracts").json()["data"]}
        assert codes == {"K-NET"}


def test_組長能標已付承辦不能(tmp_path):
    """標已付是主管層的動作；組長是主管，承辦被擋。"""
    with _client(tmp_path) as client:
        import app.store as store

        ct = _seed("contracts", {"contract_code": "K-PAY", "contract_name": "約", "amount": 100_000})
        sched = store.generate_payment_schedules(ct["id"], "installment", 1)
        _login(client, "ap03")
        assert client.post(f"/api/settle-schedule/{sched[0]['id']}", json={}).status_code == 403
        _login(client, "ap05")
        assert client.post(f"/api/settle-schedule/{sched[0]['id']}", json={}).status_code == 201


def test_角色清單含組長部長(tmp_path):
    with _client(tmp_path) as client:
        accounts = client.get("/api/auth/options").json()["data"]["accounts"]
        labels = " ".join(a["label"] for a in accounts)
        assert "組長" in labels and "部長" in labels
