from pathlib import Path
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 測試用開發密碼（不寫進程式碼；正式執行改由環境變數 / .env 提供，每人一組）
for _u in ("AP01", "AP02", "AP03"):
    os.environ.setdefault(f"{_u}_PASSWORD", "T3st!Pass")

