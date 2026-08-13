"""從既有資料補登記人員（使用者 2026-08-12：「如果系統有抓到人 可以自動幫我建立人嗎」）。

不能照單全收：實際資料裡有「蔡維庭 黎世偉 吳季凌 游穗宗」這種一格塞四個人（空白分隔），
直接建會生出一個名字很長的假人。所以拆得開的拆開、可疑的標出來、一律先預覽再建。
"""
import os

from fastapi.testclient import TestClient


def _client(tmp_path, login="ap02"):
    os.environ["SQLITE_PATH"] = str(tmp_path / "suggest.db")
    from app.main import create_app

    client = TestClient(create_app())
    if login:
        client.post("/api/auth/login", json={"username": login, "password": "T3st!Pass"})
    return client


def test_掃出沒登記的人並從來源推組別(tmp_path):
    with _client(tmp_path) as client:
        # 專案的 source 是匯入來源工作表名，實際資料長這樣：「網路組處級專案」
        client.post("/api/projects", json={
            "project_name": "骨幹汰換", "owner": "許晉豪", "source": "網路組處級專案"})
        client.post("/api/projects", json={
            "project_name": "主機更新", "owner": "林義昌", "source": "主機組處級專案"})

        data = client.get("/api/personnel-suggest").json()["data"]
        by_name = {c["name"]: c for c in data["candidates"]}
        assert by_name["許晉豪"]["group_name"] == "網路組"      # 從來源推出來
        assert by_name["林義昌"]["group_name"] == "主機組"
        assert all(c["recommend"] for c in data["candidates"])  # 正常的預設勾選
        assert "推不出來就留空" in data["note"]


def test_推不出組別就留空不瞎猜(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/projects", json={
            "project_name": "AI 案", "owner": "吳承翰", "source": "AI專案"})
        cands = client.get("/api/personnel-suggest").json()["data"]["candidates"]
        assert [c for c in cands if c["name"] == "吳承翰"][0]["group_name"] == ""


def test_共同負責人會拆開(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/projects", json={"project_name": "共同", "owner": "陳昱杉/洪似妮"})
        names = {c["name"] for c in client.get("/api/personnel-suggest").json()["data"]["candidates"]}
        assert {"陳昱杉", "洪似妮"} <= names
        assert "陳昱杉/洪似妮" not in names


def test_一格塞多人會拆開但標記要確認(tmp_path):
    """這是實際資料裡真的存在的情況（工作項負責人欄）。"""
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={"project_name": "搬遷"}).json()["data"]
        client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "訪談", "owner": "蔡維庭 黎世偉 吳季凌 游穗宗"})

        data = client.get("/api/personnel-suggest").json()["data"]
        by_name = {c["name"]: c for c in data["candidates"]}
        assert {"蔡維庭", "黎世偉", "吳季凌", "游穗宗"} <= set(by_name)
        assert "蔡維庭 黎世偉 吳季凌 游穗宗" not in by_name          # 不會建成一個假人
        assert by_name["蔡維庭"]["recommend"] is False               # 可疑的不預設勾選
        assert "空白分隔" in by_name["蔡維庭"]["suspect"]
        assert by_name["蔡維庭"]["raw_sample"] == "蔡維庭 黎世偉 吳季凌 游穗宗"   # 看得到原始值


def test_也單獨出現過的人不被一筆髒資料連坐(tmp_path):
    """實例：「蔡維庭 黎世偉 吳季凌 游穗宗」害同時也單獨掛在別處的游穗宗被標成可疑。
    只要有一次乾淨地單獨出現，名字本身就沒問題。"""
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={"project_name": "搬遷", "owner": "游穗宗"}).json()["data"]
        client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "訪談", "owner": "蔡維庭 黎世偉 吳季凌 游穗宗"})

        by_name = {c["name"]: c for c in client.get("/api/personnel-suggest").json()["data"]["candidates"]}
        assert by_name["游穗宗"]["recommend"] is True and by_name["游穗宗"]["suspect"] == ""
        assert by_name["蔡維庭"]["recommend"] is False     # 只出現在那一格裡的，仍要人確認


def test_誤填的長句不會被當人名推薦(tmp_path):
    with _client(tmp_path) as client:
        p = client.post("/api/projects", json={"project_name": "X"}).json()["data"]
        client.post(f"/api/projects/{p['id']}/items", json={
            "item_name": "Y", "owner": "由網路組協助，待確認負責人"})
        cands = client.get("/api/personnel-suggest").json()["data"]["candidates"]
        odd = [c for c in cands if not c["recommend"]]
        assert odd and any("誤填" in c["suspect"] or "確認" in c["suspect"] for c in odd)


def test_建立選定的人並且冪等(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/projects", json={
            "project_name": "骨幹", "owner": "許晉豪", "source": "網路組處級專案"})

        r = client.post("/api/personnel-suggest/create", json={"names": ["許晉豪"]}).json()["data"]
        assert r["created_count"] == 1 and r["created"][0]["group_name"] == "網路組"

        masters = client.get("/api/personnel-master?include_disabled=true").json()["data"]["masters"]
        me = [m for m in masters if m["name"] == "許晉豪"][0]
        assert me["group_name"] == "網路組" and "自動補登記" in (me["note"] or "")

        # 再按一次：已存在的跳過，不會爆錯也不會重複
        again = client.post("/api/personnel-suggest/create", json={"names": ["許晉豪"]}).json()["data"]
        assert again["created_count"] == 0 and again["skipped"] == ["許晉豪"]

        # 建完就不再出現在候選
        cands = client.get("/api/personnel-suggest").json()["data"]["candidates"]
        assert "許晉豪" not in {c["name"] for c in cands}


def test_可以個別覆蓋推測的組別(tmp_path):
    with _client(tmp_path) as client:
        client.post("/api/projects", json={
            "project_name": "骨幹", "owner": "許晉豪", "source": "網路組處級專案"})
        client.post("/api/personnel-suggest/create",
                    json={"names": ["許晉豪"], "groups": {"許晉豪": "主機組"}})
        masters = client.get("/api/personnel-master?include_disabled=true").json()["data"]["masters"]
        assert [m for m in masters if m["name"] == "許晉豪"][0]["group_name"] == "主機組"


def test_沒選人要擋下來(tmp_path):
    with _client(tmp_path) as client:
        assert client.post("/api/personnel-suggest/create", json={"names": []}).status_code == 422
