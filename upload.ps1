# CL_FEE 上傳工具：列出這次改了什麼 -> 打版本號 -> 檢查敏感檔 -> commit -> push
#
# 為什麼需要這支：
# 1. 版本號散在四個地方（後端 BACKEND_BUILD、前端 BUILD_TAG、index.html 的兩個
#    cache-bust token）。漏掉 token 的話瀏覽器會繼續用舊的 app.js，畫面看起來
#    像沒更新——這個坑已經踩過不只一次。這支一次全部改掉。
# 2. CL_FEE 是 public repo，`git add -A` 全推很危險。推之前先擋敏感檔。
# 3. 推之前要看得到「這次到底動了哪些檔、幾個檔」，而不是盲推。
#
# 邏輯放在 .ps1 而不是 .bat：批次檔以系統 ANSI（繁中 cp950/Big5）解析，
# 部分中文字的第二個位元組是反斜線，cmd 會當跳脫字元導致整行散掉。
# upload.bat 只保留純英文，負責叫起這支。

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$HERE = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $HERE

function Write-Head($text) {
    Write-Host ""
    Write-Host ("=" * 64) -ForegroundColor DarkGray
    Write-Host ("  " + $text)
    Write-Host ("=" * 64) -ForegroundColor DarkGray
}

function Quit($code) {
    Write-Host ""
    Write-Host "  按 Enter 結束..." -ForegroundColor DarkGray
    [void](Read-Host)
    exit $code
}

# ── 前置檢查 ─────────────────────────────────────────────────────────────
& git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Head "這個資料夾不是 git 儲存庫"
    Write-Host "  位置：$HERE" -ForegroundColor Yellow
    Quit 1
}

$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
if ($branch -ne "main") {
    Write-Host ""
    Write-Host "  注意：目前在分支「$branch」，不是 main。" -ForegroundColor Yellow
    Write-Host "  部署端的 update.bat 只抓 main，推到別的分支對方拿不到。"
    $go = Read-Host "  仍要繼續嗎？（Y=繼續 / 其他=取消）"
    if ($go -notmatch '^[Yy]') { Quit 0 }
}

# ── 這次改了什麼（使用者要的重點）─────────────────────────────────────────
$porcelain = @(& git status --porcelain)
if ($porcelain.Count -eq 0) {
    Write-Head "沒有任何變更，不需要上傳"
    Write-Host "  本地與上次 commit 完全相同。"
    $ahead = (& git rev-list --count "origin/$branch..$branch" 2>$null)
    if ($ahead -and [int]$ahead -gt 0) {
        Write-Host ""
        Write-Host "  但有 $ahead 個 commit 還沒推上 GitHub。" -ForegroundColor Yellow
        $p = Read-Host "  現在推嗎？（Y=推 / 其他=取消）"
        if ($p -match '^[Yy]') {
            & git push origin $branch
            if ($LASTEXITCODE -eq 0) { Write-Host "  推送完成。" -ForegroundColor Green }
        }
    }
    Quit 0
}

$added = @(); $modified = @(); $deleted = @(); $untracked = @()
foreach ($line in $porcelain) {
    $code = $line.Substring(0, 2)
    $file = $line.Substring(3).Trim('"')
    if ($code -match '\?\?')     { $untracked += $file }
    elseif ($code -match 'D')    { $deleted   += $file }
    elseif ($code -match 'A')    { $added     += $file }
    else                         { $modified  += $file }
}

Write-Head "這次的變更（共 $($porcelain.Count) 個檔案）"
function Show-Group($title, $list, $color) {
    if ($list.Count -eq 0) { return }
    Write-Host ""
    Write-Host ("  {0}（{1} 個）" -f $title, $list.Count) -ForegroundColor $color
    foreach ($f in $list) { Write-Host "    $f" }
}
Show-Group "已修改" $modified "Yellow"
Show-Group "新增（尚未納入版控）" $untracked "Green"
Show-Group "新增（已納入版控）" $added "Green"
Show-Group "已刪除" $deleted "Red"

# 有多少行變動，給個規模感
$stat = @(& git diff --shortstat)
if ($stat) { Write-Host ""; Write-Host "  程式碼變動：$($stat -join ' ')" -ForegroundColor DarkGray }

# ── 敏感檔攔截：CL_FEE 是 public repo ───────────────────────────────────
$risky = @()
foreach ($f in ($modified + $untracked + $added)) {
    if ($f -match '\.(xlsx?|xlsm|db|sqlite\d?|env|pem|key|pfx)$' -and $f -notmatch '\.env\.example$') {
        $risky += $f
    }
}
if ($risky.Count -gt 0) {
    Write-Head "警告：偵測到可能不該公開的檔案"
    Write-Host "  CL_FEE 是公開的 GitHub 儲存庫，以下檔案一旦推上去就很難清乾淨：" -ForegroundColor Red
    foreach ($f in $risky) { Write-Host "    $f" -ForegroundColor Red }
    Write-Host ""
    Write-Host "  建議：先把它們加進 .gitignore，取消這次上傳。"
    $go = Read-Host "  仍要繼續嗎？（輸入 YES 全大寫才會繼續）"
    if ($go -cne "YES") { Write-Host "  已取消。"; Quit 0 }
}

# ── 版本號 ───────────────────────────────────────────────────────────────
$mainPy = Join-Path $HERE "app\main.py"
$appJs  = Join-Path $HERE "app\web\app.js"
$html   = Join-Path $HERE "app\web\index.html"
$chlog  = Join-Path $HERE "CHANGELOG.md"

$cur = ""
if (Test-Path $mainPy) {
    $m = [regex]::Match([System.IO.File]::ReadAllText($mainPy), 'BACKEND_BUILD = "(v[0-9.]+)')
    if ($m.Success) { $cur = $m.Groups[1].Value }
}

Write-Head "版本號"
Write-Host "  目前版本：$cur"
# 預設把最後一段 +1，省得每次自己想
$suggest = ""
if ($cur -match '^v(\d+)\.(\d+)\.(\d+)$') {
    $suggest = "v{0}.{1}.{2}" -f $Matches[1], ([int]$Matches[2] + 1), 0
}
Write-Host "  建議下一版：$suggest" -ForegroundColor DarkGray
Write-Host ""
$newVer = Read-Host "  要打的版本號（直接按 Enter 用 $suggest）"
if ([string]::IsNullOrWhiteSpace($newVer)) { $newVer = $suggest }
if ($newVer -notmatch '^v\d+\.\d+\.\d+$') {
    Write-Host "  版本號格式不對，要像 v0.20.0。已取消。" -ForegroundColor Red
    Quit 1
}

$desc = Read-Host "  這次改了什麼（一句話，會寫進版本徽章與 CHANGELOG）"
if ([string]::IsNullOrWhiteSpace($desc)) {
    Write-Host "  說明不能空白，否則之後看不懂這版做了什麼。已取消。" -ForegroundColor Red
    Quit 1
}

$stamp   = Get-Date -Format "yyyy-MM-dd HH:mm"
$tag     = "$newVer · $stamp · $desc"
$token   = "v" + ($newVer.TrimStart('v') -replace '\.', '-')   # v0.20.0 -> v0-20-0

# ── 先確認再動檔案 ───────────────────────────────────────────────────────
# 刻意把確認放在改版本號之前：取消時工作區要保持原狀，不能留下改到一半的版本號。
Write-Head "即將上傳"
Write-Host "  版本：$cur  ->  $newVer"
Write-Host "  說明：$desc"
Write-Host "  分支：$branch  ->  GitHub"
Write-Host "  檔案：$($porcelain.Count) 個"
Write-Host ""
Write-Host "  提醒：commit 前會自動跑完整測試，大約需要 5 分鐘，請不要關視窗。" -ForegroundColor DarkGray
Write-Host ""
$ok = Read-Host "  確定要上傳嗎？（Y=上傳 / 其他=取消）"
if ($ok -notmatch '^[Yy]') {
    Write-Host ""
    Write-Host "  已取消，沒有改動任何檔案。" -ForegroundColor Yellow
    Quit 0
}

# 四個位置一起改，漏一個就會有人看到舊畫面
$bumped = @()
if (Test-Path $mainPy) {
    $t = [System.IO.File]::ReadAllText($mainPy)
    $t = [regex]::Replace($t, 'BACKEND_BUILD = "[^"]*"', 'BACKEND_BUILD = "' + $tag + '"')
    [System.IO.File]::WriteAllText($mainPy, $t)
    $bumped += "app\main.py (BACKEND_BUILD)"
}
if (Test-Path $appJs) {
    $t = [System.IO.File]::ReadAllText($appJs)
    $t = [regex]::Replace($t, 'const BUILD_TAG = "[^"]*";', 'const BUILD_TAG = "' + $tag + '";')
    [System.IO.File]::WriteAllText($appJs, $t)
    $bumped += "app\web\app.js (BUILD_TAG)"
}
if (Test-Path $html) {
    $t = [System.IO.File]::ReadAllText($html)
    $t = [regex]::Replace($t, '\?v=v[0-9-]+', '?v=' + $token)
    [System.IO.File]::WriteAllText($html, $t)
    $bumped += "app\web\index.html (cache token -> ?v=$token)"
}
if (Test-Path $chlog) {
    $t = [System.IO.File]::ReadAllText($chlog)
    $entry = "## $newVer — $stamp`r`n- $desc`r`n`r`n"
    $idx = $t.IndexOf("`n---`n")
    if ($idx -ge 0) {
        $cut = $idx + 5
        $t = $t.Substring(0, $cut) + "`r`n" + $entry + $t.Substring($cut).TrimStart("`r", "`n")
    } else {
        $t = $t.TrimEnd() + "`r`n`r`n" + $entry
    }
    [System.IO.File]::WriteAllText($chlog, $t)
    $bumped += "CHANGELOG.md"
}

Write-Host ""
Write-Host "  已更新版本號：" -ForegroundColor Green
foreach ($b in $bumped) { Write-Host "    $b" }

# ── commit + push ────────────────────────────────────────────────────────
# 刻意不用 git add -A。CL_FEE 是公開 repo，全加會把交接摘要、本機資料庫這類
# 只該留在本機的東西一起推上去。已追蹤的檔案照收，全新的檔案要個別點頭。
Write-Host ""
Write-Host "  加入已追蹤檔案的變更..."
& git add -u

if ($untracked.Count -gt 0) {
    Write-Host ""
    Write-Host "  以下是全新的檔案（目前不在版控裡）：" -ForegroundColor Yellow
    foreach ($f in $untracked) { Write-Host "    $f" }
    Write-Host ""
    Write-Host "  這些會永久留在公開的 GitHub 歷史裡，確定都能公開再加入。" -ForegroundColor DarkGray
    $addNew = Read-Host "  要一起上傳嗎？（Y=全部加入 / 其他=這次略過）"
    if ($addNew -match '^[Yy]') {
        foreach ($f in $untracked) { & git add -- $f }
        Write-Host "  已加入 $($untracked.Count) 個新檔案。"
    } else {
        Write-Host "  這次略過新檔案，只上傳既有檔案的修改。"
    }
}

$final = @(& git diff --cached --name-only)
if ($final.Count -eq 0) {
    Write-Head "沒有東西可以上傳"
    Write-Host "  所有變更都被略過了（可能全是未納入版控的新檔案）。"
    Quit 0
}

Write-Host "  測試與 commit 中（約 5 分鐘）..."
& git commit -m "$desc ($newVer)"
if ($LASTEXITCODE -ne 0) {
    Write-Head "commit 失敗"
    Write-Host "  多半是 commit 前的檢查沒過（測試失敗、或偵測到寫死的密碼）。" -ForegroundColor Yellow
    Write-Host "  上面的訊息會寫明原因；修好後再跑一次這支。"
    Quit 1
}

Write-Host "  推送到 GitHub..."
& git push origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Head "推送失敗"
    Write-Host "  commit 已經完成，只是還沒推上去。" -ForegroundColor Yellow
    Write-Host "  常見原因：沒有網路、或 GitHub 登入憑證過期。"
    Write-Host "  網路恢復後重跑這支，或直接執行：git push origin $branch"
    Quit 1
}

Write-Head "上傳完成"
Write-Host "  版本：$newVer" -ForegroundColor Green
Write-Host "  檔案：$($final.Count) 個"
Write-Host ""
Write-Host "  對方現在可以執行 update.bat 取得這一版。"
Write-Host "  提醒：對方開啟畫面後若還是舊的，請按 Ctrl+Shift+R 強制重新整理。"
Quit 0
