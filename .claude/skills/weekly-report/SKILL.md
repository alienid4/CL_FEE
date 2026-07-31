---
name: weekly-report
description: CL_FEE 週進度報告產生器。當使用者說「產週報」、「寫這禮拜的進度報告」、「進度報告要更新」、「要寄報告給主管」、「開發進度報告」、「報告更新到最新版」時觸發。產出三樣東西：更新後的 docs\開發進度報告.html（七個頁籤＋流程圖橘框標本次新完成）、docs\開發進度報告_對照表.xlsx（進度對照＋WBS 全項目，主管可自己篩選排序），以及可直接貼進 Outlook 的信件主旨與內文。信一律由使用者自己寄，不代寄。
---

# CL_FEE 週進度報告

完整規格與信件模板在 **`AI\週報告_TEMPLATE.md`**，動手前先讀那份。以下是執行摘要。

## 鐵則

1. **改報告前先備份**：`copy docs\開發進度報告.html docs\報告存檔\開發進度報告_YYYY-MM-DD.html`
   不備份 = 下次沒有東西可以做前後對比。
2. **信不要代寄**。只把主旨與內文拎出來給使用者，他自己發。
3. **收信的是助理和主管，不是工程師**：不寫節點編號、資料表名、內部術語。
   用「他們會遇到的事」講（「合約要付多少、還欠多少現在算得準」而不是「Payment Schedule 拆分」）。
4. **數字要有對照**：54% → 85%，不是只寫 85%。
5. 報告是中文 HTML：**不要用 PowerShell 的 `Get-Content`／`Set-Content` 改**（會加 BOM／壞編碼），
   用 Edit 工具或 `py` 腳本。

## 流程

```
# 1 備份上一版
copy docs\開發進度報告.html docs\報告存檔\開發進度報告_YYYY-MM-DD.html

# 2 抓數字與流程圖差異（<上次> = 上次寄出那份的存檔）
py scripts\weekly_report_tools.py stats     <上次> docs\開發進度報告.html
py scripts\weekly_report_tools.py flow-diff <上次> docs\開發進度報告.html
git log --date=short --pretty=format:"%ad %s" -40

# 3 改七個頁籤（摘要 / 開發前後對比 / WBS 進度 / 架構 / 進度報告 / 待拍板 / 更新紀錄）
#   版號日期三處要改：頁首 eyebrow、masthead 回報期間、頁尾「產生於」
py scripts\weekly_report_tools.py mark docs\開發進度報告.html <flow-diff 給的行號>

# 4 產出前檢查（四個 OK 才算過）
py scripts\weekly_report_tools.py verify docs\開發進度報告.html

# 5 產第二個附件：Excel（HTML 給人看，Excel 給人用——主管要自己篩選、排序、貼進他的報表）
py scripts\weekly_report_tools.py xlsx <上次> docs\開發進度報告.html docs\開發進度報告_對照表.xlsx
```

6. **Excel 一定要重算過再交**：openpyxl 寫的公式沒有快取值，不重算的話別人開起來
   差額欄可能是空的。這台機器的 LibreOffice recalc 腳本在 Windows 跑不起來
   （`socket.AF_UNIX` 不存在），改用 Excel COM：

```powershell
$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false
$wb = $x.Workbooks.Open("C:\AiProject\CL_FEE\docs\開發進度報告_對照表.xlsx")
$x.CalculateFullRebuild(); $wb.Save(); $wb.Close($true); $x.Quit()
```

   重算後確認沒有 `#` 開頭的錯誤格，並抽查一格差額對不對（例：整體 54%→85%，差額要是 31%）。
   另外 Excel 的「WBS 全項目」列數與各狀態數要跟 HTML 摘要頁的四態統計對得起來——
   對不上表示有一邊沒更新到。

7. 用 `AI\週報告_TEMPLATE.md` 第四節的模板寫信，主旨＋內文直接輸出在對話裡。
8. 用 SendUserFile 把 HTML（`display: render`）與 Excel（`display: attach`）送給使用者預覽。

## 附件必備的七個頁籤

摘要 · 開發前後對比 · WBS 進度 · 架構 · 進度報告 · 待拍板 · 更新紀錄

「開發前後對比」是左右並排：左＝上次寄出那份的狀態、右＝現在，六個階段各一條進度條，
右邊標 +N。流程圖裡本次新完成的節點用橘框（#d9860b），一眼看得出這週補在哪。
