# Auth And Email Rules

公司內部系統預設要考慮 AD 登入與 Email 通知。

## AD 登入

- 預設支援 AD / LDAP 登入。
- 需要測試登入設定。
- 需要角色 mapping。
- 需要本機 emergency admin 或替代登入策略。
- 登入失敗不得洩漏帳號是否存在。

## Email 設定

- SMTP / Graph API / 內部郵件閘道要放管理介面。
- 必須有測試寄信功能。
- 必須有寄信失敗紀錄。
- 寄信設定不得寫死在程式碼。
- 測試信不得包含敏感資料。

