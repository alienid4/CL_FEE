from pathlib import Path
import os
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 測試用開發密碼（不寫進程式碼；正式執行改由環境變數 / .env 提供，每人一組）
for _u in ("AP01", "AP02", "AP03", "AP04", "AP05", "AP06", "ADMIN"):
    os.environ.setdefault(f"{_u}_PASSWORD", "T3st!Pass")

# 測試一律走「要驗密碼」那條路。
# app/main.py 會讀專案根目錄的 .env，而這台開發機的 .env 裡有 PILOT_PASSWORDLESS=1
# （試辦模式：選好角色不用密碼就能登入）。被它蓋到的話，「改完密碼舊密碼要失效」
# 這類測試會全部假綠——因為根本沒在驗密碼。conftest 比 app.main 早載入，
# 加上 _load_dotenv 是 setdefault，所以這裡先佔住就不會被 .env 覆寫。
# 專門測免密碼的 test_passwordless_login.py 自己會把它設成 1，不受影響。
os.environ.setdefault("PILOT_PASSWORDLESS", "0")

