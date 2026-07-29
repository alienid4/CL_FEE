"""需求書 §4 審核關卡：核准以外的三條路——退回補件／併入既有案／拒絕建立。

三者的共同原則是「不刪資料」：
  退件要能補完再送（沿用原暫時號，不用重開一件）
  併案要留得住「這兩件本來是同一件」，而且底下的資料要跟著搬過去
  拒絕也要留申請紀錄（停用會讓它看起來像資料被藏起來）
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "gate.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def _pending(client, code, title="案件"):
    """建一件並送到『待複核』。"""
    case = client.post("/api/cases", json={"case_code": code, "title": title}).json()["data"]
    client.post(f"/api/cases/{case['id']}/submit")
    return case


def _find(client, case_id):
    return next(c for c in client.get("/api/cases").json()["data"] if c["id"] == case_id)


def test_退回補件帶原因且可補完再送(tmp_path):
    with _client(tmp_path) as client:
        case = _pending(client, "R-1", "缺附件的案")
        r = client.post(f"/api/cases/{case['id']}/return", json={"reason": "缺簽呈附件，請補上"})
        assert r.status_code == 200, r.text
        after = r.json()["data"]
        assert after["status"] == "returned"
        assert after["review_note"] == "缺簽呈附件，請補上"
        assert after["seq"] == 0 and after["temp_seq"] == case["temp_seq"]  # 沿用原暫時號，沒配正式號

        # 補完直接再送，不用重開一件
        again = client.post(f"/api/cases/{case['id']}/submit")
        assert again.status_code == 200, again.text
        assert again.json()["data"]["status"] == "pending_review"


def test_退件沒寫原因要擋(tmp_path):
    """不寫原因，申請人不知道要補什麼。"""
    with _client(tmp_path) as client:
        case = _pending(client, "R-2")
        assert client.post(f"/api/cases/{case['id']}/return", json={"reason": "   "}).status_code == 422


def test_駁回留下申請紀錄而不是藏起來(tmp_path):
    with _client(tmp_path) as client:
        case = _pending(client, "R-3", "不該立案的")
        r = client.post(f"/api/cases/{case['id']}/reject", json={"reason": "非本部門權責"})
        assert r.status_code == 200, r.text
        assert r.json()["data"]["status"] == "rejected"
        row = _find(client, case["id"])                 # 仍查得到（不是 disabled、也沒被刪）
        assert row["review_note"] == "非本部門權責"
        assert row["seq"] == 0                          # 沒吃掉正式號


def test_駁回沒寫理由要擋(tmp_path):
    with _client(tmp_path) as client:
        case = _pending(client, "R-4")
        assert client.post(f"/api/cases/{case['id']}/reject", json={"reason": ""}).status_code == 422


def test_併案會把底下資料一起搬過去(tmp_path):
    """重點不只是標記，而是關聯要留得住：預算/合約/簽呈等要跟著轉到目標案。"""
    with _client(tmp_path) as client:
        keep = client.post("/api/cases", json={"case_code": "M-KEEP", "title": "既有的冷氣維護案"}).json()["data"]
        dup = _pending(client, "M-DUP", "重複申請的冷氣維護")
        client.post("/api/budgets", json={"budget_code": "MB-1", "category": "基礎建設",
                                          "amount": 100_000, "case_id": dup["id"]})
        client.post("/api/contracts", json={"contract_code": "MK-1", "contract_name": "冷氣保養",
                                            "amount": 80_000, "case_id": dup["id"]})

        r = client.post(f"/api/cases/{dup['id']}/merge",
                        json={"target_case_id": keep["id"], "reason": "與 M-KEEP 同一件"})
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["status"] == "merged"
        assert d["merged_into_case_id"] == keep["id"]     # 看得出併到哪一件
        assert d["moved"] == {"budgets": 1, "contracts": 1}

        # 資料真的掛到目標案底下了
        c360 = client.get(f"/api/cases/{keep['id']}/360").json()["data"]
        assert [b["budget_code"] for b in c360["budgets"]] == ["MB-1"]
        assert [k["contract_code"] for k in c360["contracts"]] == ["MK-1"]


def test_不能併入自己或不存在的案(tmp_path):
    with _client(tmp_path) as client:
        case = _pending(client, "M-SELF")
        assert client.post(f"/api/cases/{case['id']}/merge",
                           json={"target_case_id": case["id"]}).status_code == 422
        assert client.post(f"/api/cases/{case['id']}/merge",
                           json={"target_case_id": 99999}).status_code == 422


def test_不能併入已被併走或已駁回的案(tmp_path):
    """目標本身已經不是有效案件，併過去會接不下去。"""
    with _client(tmp_path) as client:
        dead = _pending(client, "M-DEAD")
        client.post(f"/api/cases/{dead['id']}/reject", json={"reason": "不立案"})
        newone = _pending(client, "M-NEW")
        r = client.post(f"/api/cases/{newone['id']}/merge", json={"target_case_id": dead["id"]})
        assert r.status_code == 422, r.text


def test_已核准的案不能再退件或駁回(tmp_path):
    with _client(tmp_path) as client:
        case = _pending(client, "R-DONE")
        client.post("/api/auth/login", json={"username": "ap04", "password": "T3st!Pass"})
        client.post(f"/api/cases/{case['id']}/approve")
        assert client.post(f"/api/cases/{case['id']}/return", json={"reason": "x"}).status_code == 409
        assert client.post(f"/api/cases/{case['id']}/reject", json={"reason": "x"}).status_code == 409


def test_承辦不能自己退件駁回併案(tmp_path):
    """審核動作限主管/助理，承辦只能補件再送。"""
    with _client(tmp_path) as client:
        case = _pending(client, "R-PERM")
        client.post("/api/auth/login", json={"username": "ap03", "password": "T3st!Pass"})
        assert client.post(f"/api/cases/{case['id']}/return", json={"reason": "x"}).status_code == 403
        assert client.post(f"/api/cases/{case['id']}/reject", json={"reason": "x"}).status_code == 403
        assert client.post(f"/api/cases/{case['id']}/merge", json={"target_case_id": 1}).status_code == 403


def test_審核動作都寫進稽核軌跡(tmp_path):
    with _client(tmp_path) as client:
        case = _pending(client, "R-AUDIT")
        client.post(f"/api/cases/{case['id']}/return", json={"reason": "補件"})
        logs = client.get("/api/audit-logs", params={"table_name": "cases", "row_id": case["id"]}).json()["data"]
        assert any(x["action"] == "return" for x in logs)
