# 給 Codex 的起始提示

你現在要接手「費用合約控管系統」開發。

請先閱讀專案目錄中的以下文件：

1. README_Codex_接手總覽_v2.0.md
2. docs/README_DEV_Codex_Python_MSSQL_v2.0.md
3. docs/WBS_專案進度_v2.0.md
4. skills/PROJECT_SKILL_費用合約控管_v2.0.md
5. skills/COMMON_SKILL_套用摘要_v2.0.md
6. docs/API_DB_UI_開發重點_v2.0.md

請注意：

- 本案正式技術方向是 Python + MSSQL。
- 舊文件若提到 Node.js CommonJS 或 src/server.cjs，請視為歷史規格，除非使用者再次要求，否則不要採用。
- 系統名稱是「費用合約控管系統」。
- 資料庫名稱建議 FeeContractControl。
- AP 帳號建議 fee_contract_app。
- AP 帳號不需要 SYSADMIN(SA)。
- 必須提供 /health。
- 必須提供 OpenAPI / Swagger。
- 每次交付都要更新 WBS 完成百分比。

第一個任務請先產生 Python FastAPI + MSSQL 專案骨架，不要一次大量實作所有功能。

請先回覆：

1. 你已讀取哪些文件。
2. 你理解的系統目標。
3. 你建議的第一批檔案結構。
4. 第一批要實作的最小功能。
5. WBS 進度如何更新。

然後再等我確認後開始產生程式碼。
