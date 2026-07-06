# Company Codex Enterprise Profile

公司環境預設為 PC 上使用 VS Code / Codex Enterprise，透過 Linux 主機進行開發、測試與部署。

## 預設技術政策

- 未指定資料庫時，正式環境預設 Microsoft SQL Server。
- 原型可用 JSON / SQLite，但必須保留可改 MSSQL 的分層。
- 後端不得把資料庫連線、Token、密碼寫死。
- 診斷輸出必須可去敏，預設放 `/tmp` 或本機 temp。
- 公司 Linux 可能無法上網，安裝腳本必須支援離線或內部來源。

## Codex 使用政策

- 小修可走快速驗證。
- 大修、資料結構、權限、安全、安裝流程與發版必須走完整驗證。
- 需要公司環境資訊時，先提供可去敏指令，不要猜。
- 不要因為使用者要求快就跳過必要檢查。

