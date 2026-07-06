# Definition Of Ready / Done

## Definition Of Ready

需求進入開發前，至少要有：

- 需求目標。
- 影響畫面、API、資料表或 job。
- 主要使用者。
- 成功條件。
- 失敗或錯誤情境。
- 測試方式。
- 是否涉及敏感資料。
- 是否需要 migration、部署、rollback。

## Definition Of Done

需求完成時，至少要有：

- 行為已改好。
- 有測試或可重現驗證。
- 相關文件已更新。
- 風險與限制已說明。
- release note 已寫。
- 未新增敏感資料外洩。
- 若有破壞性操作，已記錄人工核准。

## 不算完成的情況

- 只改了畫面，資料或 API 沒跟上。
- 只修了範例資料，正式資料流程沒修。
- 沒跑測試卻說完成。
- 根本原因不明，只靠暫時 workaround。
- 沒處理 rollback 或資料備份。
