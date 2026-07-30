"""WBS 自動彙總（助理文件 2026-07-29 的算法）。

  WBS 進度%  ＝ 子項目完成數 ÷ 子項目總數（人只填兩個數字）
  專案完成%  ＝ 所有 WBS 的子項目完成數 ÷ 總數（不是各 WBS 進度的平均——子項多寡權重不同）
  專案起訖日 ＝ 第一個 WBS 的開始日、最後一個 WBS 的完成日
  專案燈號   ＝ 所有 WBS 燈號取最嚴重（紅>黃>綠>白>灰）
  燈號改紅或黃時，關鍵風險點必填
"""
import os
from datetime import date, timedelta

from fastapi.testclient import TestClient

_PW = os.environ.get("AP02_PASSWORD", "")


def _client(tmp_path):
    os.environ["SQLITE_PATH"] = str(tmp_path / "wbs.db")
    from app.main import create_app

    client = TestClient(create_app())
    client.post("/api/auth/login", json={"username": "ap02", "password": _PW})
    return client


def _in(days):
    return (date.today() + timedelta(days=days)).isoformat()


def _project(client, name="彙總測試專案"):
    return client.post("/api/projects", json={"project_name": name}).json()["data"]


def _item(client, pid, **kw):
    r = client.post(f"/api/projects/{pid}/items", json={"item_name": kw.pop("name", "工作項"), **kw})
    return r


def _proj(client, pid):
    return next(p for p in client.get("/api/projects").json()["data"] if p["id"] == pid)


def test_WBS進度由子項目數自動算(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        r = _item(client, p["id"], name="設備採購", sub_total=8, sub_done=2,
                  start_date=_in(-10), end_date=_in(20), risk_note="x")
        assert r.status_code == 201, r.text
        assert r.json()["data"]["progress"] == 25.0        # 2/8


def test_完成數不能大於總數(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        assert _item(client, p["id"], sub_total=3, sub_done=5).status_code == 422


def test_專案完成度按子項目加權不是各WBS平均(tmp_path):
    """20 個子項完成 10 個 ＋ 1 個子項完成 1 個 → 11/21 ≒ 52.4%，不是 (50%+100%)/2 ＝ 75%。"""
    with _client(tmp_path) as client:
        p = _project(client)
        _item(client, p["id"], name="大項", sub_total=20, sub_done=10, start_date=_in(-5), end_date=_in(30))
        _item(client, p["id"], name="小項", sub_total=1, sub_done=1)
        assert _proj(client, p["id"])["progress"] == 52.4


def test_專案起訖日取第一個開始與最後一個完成(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        _item(client, p["id"], name="前段", sub_total=1, sub_done=1, start_date="2026-03-01", end_date="2026-05-31")
        _item(client, p["id"], name="後段", sub_total=1, sub_done=1, start_date="2026-06-01", end_date="2026-12-31")
        row = _proj(client, p["id"])
        assert row["start_date"] == "2026-03-01"
        assert row["end_date"] == "2026-12-31"


def test_專案燈號取最嚴重(tmp_path):
    """一項如期（綠）＋一項已過完成日（紅）→ 專案是紅。"""
    with _client(tmp_path) as client:
        p = _project(client)
        _item(client, p["id"], name="正常項", sub_total=10, sub_done=5, start_date=_in(-5), end_date=_in(60))
        _item(client, p["id"], name="逾期項", sub_total=10, sub_done=1,
              start_date=_in(-60), end_date=_in(-1), risk_note="廠商延遲交貨")
        assert _proj(client, p["id"])["rag_status"] == "已延遲"


def test_燈號自動判定五色(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        # 灰＝已完成
        assert _item(client, p["id"], name="做完了", sub_total=4, sub_done=4).json()["data"]["rag"] == "gray"
        # 白＝還沒到開始日、進度 0
        assert _item(client, p["id"], name="還沒開始", sub_total=4, sub_done=0,
                     start_date=_in(30), end_date=_in(60)).json()["data"]["rag"] == "white"
        # 紅＝過了完成日還沒做完
        assert _item(client, p["id"], name="逾期", sub_total=4, sub_done=1, start_date=_in(-30),
                     end_date=_in(-1), risk_note="卡住").json()["data"]["rag"] == "red"
        # 綠＝進度跟得上時間軸
        assert _item(client, p["id"], name="如期", sub_total=10, sub_done=9,
                     start_date=_in(-5), end_date=_in(90)).json()["data"]["rag"] == "green"


def test_紅黃燈必填關鍵風險點(tmp_path):
    """助理文件：承辦把燈號改成紅或黃時，關鍵風險點必填。"""
    with _client(tmp_path) as client:
        p = _project(client)
        # 自動判成紅燈但沒填風險點 → 擋下
        r = _item(client, p["id"], name="逾期沒說明", sub_total=4, sub_done=0,
                  start_date=_in(-30), end_date=_in(-1))
        assert r.status_code == 422
        assert "關鍵風險點" in r.json()["detail"]
        # 補上就過
        assert _item(client, p["id"], name="逾期有說明", sub_total=4, sub_done=0,
                     start_date=_in(-30), end_date=_in(-1), risk_note="等廠商到貨").status_code == 201


def test_自動燈號會隨進度重算不會卡在舊值(tmp_path):
    """實測抓到的洞：自動判出來的燈號存進資料庫後，不能被誤當成「人工指定」，
    否則子項目做完了燈號還掛著黃燈。"""
    with _client(tmp_path) as client:
        p = _project(client)
        it = _item(client, p["id"], name="會做完的項", sub_total=20, sub_done=10,
                   start_date="2026-03-01", end_date=_in(45), risk_note="原廠交期延後").json()["data"]
        assert it["rag"] == "yellow"                                    # 落後時間軸→黃
        r = client.patch(f"/api/project-items/{it['id']}", json={"sub_done": 20})
        assert r.status_code == 200, r.text
        assert r.json()["data"]["progress"] == 100.0
        assert r.json()["data"]["rag"] == "gray"                        # 做完就該變灰，不是留著黃
        assert _proj(client, p["id"])["rag_status"] == "已完成"


def test_人工指定的燈號不會被系統覆蓋(tmp_path):
    """需求書 §6「燈號可由系統判斷，也保留人工調整」——人工標了就不該被自動判定蓋掉。"""
    with _client(tmp_path) as client:
        p = _project(client)
        it = _item(client, p["id"], name="人工標紅", sub_total=10, sub_done=1, start_date=_in(-3),
                   end_date=_in(90), rag="紅燈", risk_note="關鍵人力離職").json()["data"]
        assert it["rag"] == "red"
        # 改子項數（自動判會是綠/黃），人工的紅燈要留著
        r = client.patch(f"/api/project-items/{it['id']}", json={"sub_done": 9})
        assert r.json()["data"]["rag"] == "red"
        # 把燈號清空＝交回系統自動判
        r2 = client.patch(f"/api/project-items/{it['id']}", json={"rag": ""})
        assert r2.json()["data"]["rag"] in ("green", "yellow", "gray")


def test_人工指定燈號可覆蓋自動判定(tmp_path):
    """燈號「可由系統判斷，也保留人工調整」（需求書 §6）。人工填中文也吃。"""
    with _client(tmp_path) as client:
        p = _project(client)
        r = _item(client, p["id"], name="人工標黃", sub_total=10, sub_done=9,
                  start_date=_in(-5), end_date=_in(90), rag="有延遲風險", risk_note="關鍵人力被抽調")
        assert r.status_code == 201, r.text
        assert r.json()["data"]["rag"] == "yellow"        # 中文轉成內部代碼
        assert _proj(client, p["id"])["rag_status"] == "有延遲風險"


def test_改一項會重算專案彙總(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        it = _item(client, p["id"], name="項", sub_total=10, sub_done=2,
                   start_date=_in(-5), end_date=_in(60)).json()["data"]
        assert _proj(client, p["id"])["progress"] == 20.0
        client.patch(f"/api/project-items/{it['id']}", json={"sub_done": 7})
        assert _proj(client, p["id"])["progress"] == 70.0


def test_停用或刪除一項也會重算(tmp_path):
    with _client(tmp_path) as client:
        p = _project(client)
        a = _item(client, p["id"], name="留著", sub_total=10, sub_done=10).json()["data"]
        b = _item(client, p["id"], name="要刪的", sub_total=10, sub_done=0,
                  start_date=_in(30), end_date=_in(60)).json()["data"]
        assert _proj(client, p["id"])["progress"] == 50.0      # 10/20
        client.delete(f"/api/project-items/{b['id']}")
        assert _proj(client, p["id"])["progress"] == 100.0     # 只剩做完的那項


def test_沒有WBS就不動專案原值(tmp_path):
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={
            "project_name": "手填進度的專案", "progress": 42, "rag_status": "如期執行"}).json()["data"]
        assert _proj(client, p["id"])["progress"] == 42        # 還沒拆 WBS，不要被歸零
