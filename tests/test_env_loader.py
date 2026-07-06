"""切片 0 驗收測試：.env 載入器（修好密碼移出後 app 讀不到密碼的問題）。"""
import os

from app import main


def test_load_dotenv_parses_and_respects_existing_env(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'DEMO_ENV_A="hello"\n'
        "# 這是註解，應被略過\n"
        "\n"
        "DEMO_ENV_B=plain\n"
        "DEMO_ENV_PRE=fromfile\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DEMO_ENV_A", raising=False)
    monkeypatch.delenv("DEMO_ENV_B", raising=False)
    monkeypatch.setenv("DEMO_ENV_PRE", "fromenv")  # 已存在，應優先

    main._load_dotenv(env_file)

    assert os.environ["DEMO_ENV_A"] == "hello"        # 去除引號
    assert os.environ["DEMO_ENV_B"] == "plain"
    assert os.environ["DEMO_ENV_PRE"] == "fromenv"    # setdefault 不覆寫已存在者
