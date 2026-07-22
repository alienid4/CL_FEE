# CL_FEE 服務控制台
#
# 為什麼邏輯放在 .ps1 而不是 .bat：
# 批次檔是用系統 ANSI 編碼（繁中為 cp950/Big5）解析的，而 Big5 有部分中文字的
# 第二個位元組正好是反斜線，cmd 會當成跳脫字元，整行指令就散掉。中文訊息寫在
# .bat 裡遲早會炸。PowerShell 走 UTF-8，沒有這個問題，也有真正的錯誤處理。
# service.bat 只保留純英文，負責把這支叫起來。

# 用 Continue 而非 Stop：這支大量呼叫外部程式（python/netstat/git），而 PowerShell 5.1
# 在對原生程式重導 stderr 時會把輸出包成 ErrorRecord。搭配 Stop 會變成終止性錯誤，
# 整支腳本瞬間結束、視窗跟著關掉，使用者什麼都看不到。改為自己檢查離開碼。
$ErrorActionPreference = "Continue"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# 任何沒被預期到的錯誤都要看得見，否則就變成「點下去閃一下就不見」。
trap {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  發生未預期的錯誤" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "  訊息：$($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "  位置：$($_.InvocationInfo.ScriptName):$($_.InvocationInfo.ScriptLineNumber)"
    Write-Host "  程式碼：$($_.InvocationInfo.Line.Trim())"
    Write-Host ""
    Write-Host "  請把上面的訊息回報給維護人員。"
    Write-Host ""
    Write-Host "  按 Enter 結束..." -ForegroundColor DarkGray
    [void](Read-Host)
    exit 1
}

$HERE     = Split-Path -Parent $MyInvocation.MyCommand.Path

# 程式（app\）可能在兩種位置，取決於使用者怎麼拿到這份程式碼：
#   1. 完整包：service.bat 跟 app\ 解壓在同一層 → app 就在 $HERE 底下。
#   2. 從 GitHub clone / 下載 ZIP：service.bat 在 notebook-package\ 裡，但 app\
#      在 repo 根目錄（notebook-package\app\ 被 .gitignore 排除，clone 不會帶）
#      → app 在 $HERE 的上一層。
# 舊版寫死只找 $HERE，所以第 2 種情況一開就報「找不到 app\main.py」，錯誤訊息還
# 叫使用者「把 service.bat 跟 app 放一起」——但在 repo 裡它們本來就刻意分開，
# 使用者照著做也沒用。這裡自動往上找一層，讓兩種擺法都能直接雙擊跑。
$APPROOT = $HERE
if (-not (Test-Path (Join-Path $APPROOT "app\main.py"))) {
    $parent = Split-Path -Parent $HERE
    if ($parent -and (Test-Path (Join-Path $parent "app\main.py"))) { $APPROOT = $parent }
}

$PORT     = 8888
# 紀錄檔留在 service.bat 旁邊（$HERE），不跟著 app 走。兩種擺法下 logs\ 都被
# .gitignore 蓋到，且維護時「報告就在我雙擊的檔案旁邊」最好找。
$LOGDIR   = Join-Path $HERE "logs"
$LOGFILE  = Join-Path $LOGDIR "service.log"
$DIAGFILE = Join-Path $LOGDIR "診斷報告.txt"

if (-not (Test-Path $LOGDIR)) { New-Item -ItemType Directory -Path $LOGDIR | Out-Null }

function Write-Head($text) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor DarkGray
    Write-Host ("  " + $text)
    Write-Host ("=" * 60) -ForegroundColor DarkGray
}

function Pause-Back {
    Write-Host ""
    Write-Host "  按 Enter 回到選單..." -ForegroundColor DarkGray
    [void](Read-Host)
}

# ── 找一個真的能執行的 Python ────────────────────────────────────────────
# Windows 常見的坑：「python」指到微軟商店的空殼程式，它不執行任何東西就結束，
# 所以不能只看 Get-Command 找不找得到，一定要實際跑跑看拿得到版本才算數。
# 每個候選都要通過這個驗證，商店空殼會因為印不出版本而被跳過。
function Test-PyExe {
    param([string]$Exe, [string[]]$PyArgs = @())
    if (-not $Exe) { return $null }
    try {
        $v = & $Exe @($PyArgs + @("--version")) 2>$null
        if ($LASTEXITCODE -eq 0 -and $v -match "Python\s+3") {
            return [pscustomobject]@{ Exe = $Exe; Args = $PyArgs; Version = "$v".Trim() }
        }
    } catch {}
    return $null
}

# 四層策略，因為「Python 裝了但沒設 PATH」是公司機器的常態：
#   1. 手動指定（python_path.txt / .env 的 PYTHON_EXE）：裝在非標準路徑時最可靠。
#   2. PATH 上的 py / python / python3：最快，多數機器走這條。
#   3. Windows 登錄檔：安裝程式會登記 InstallPath，不管有沒有設 PATH 都查得到，
#      這是「正常安裝但沒進 PATH」的主要救援。
#   4. 掃常見安裝目錄：登錄檔也沒有時的最後手段。
function Find-Python {
    # 1. 手動指定 ---------------------------------------------------------
    $override = $null
    $ptxt = Join-Path $HERE "python_path.txt"
    if (Test-Path $ptxt) {
        $line = Get-Content -LiteralPath $ptxt -ErrorAction SilentlyContinue |
                Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") } | Select-Object -First 1
        if ($line) { $override = $line.Trim().Trim('"') }
    }
    if (-not $override) {
        $envFile = Join-Path $APPROOT ".env"
        if (Test-Path $envFile) {
            $m = Select-String -LiteralPath $envFile -Pattern '^\s*PYTHON_EXE\s*=\s*(.+)$' | Select-Object -First 1
            if ($m) { $override = $m.Matches[0].Groups[1].Value.Trim().Trim('"') }
        }
    }
    if ($override) {
        $r = Test-PyExe $override
        if ($r) { return $r }
    }

    # 2. PATH -------------------------------------------------------------
    foreach ($cand in @(@{Exe="py"; Args=@("-3")}, @{Exe="python"; Args=@()}, @{Exe="python3"; Args=@()})) {
        $r = Test-PyExe $cand.Exe $cand.Args
        if ($r) { return $r }
    }

    # 3. 登錄檔 -----------------------------------------------------------
    foreach ($hive in @("HKLM:\SOFTWARE\Python\PythonCore",
                        "HKCU:\SOFTWARE\Python\PythonCore",
                        "HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore")) {
        if (-not (Test-Path $hive)) { continue }
        foreach ($ver in (Get-ChildItem $hive -ErrorAction SilentlyContinue | Sort-Object PSChildName -Descending)) {
            try {
                $ipKey = Join-Path $ver.PSPath "InstallPath"
                $installPath = (Get-Item -LiteralPath $ipKey -ErrorAction SilentlyContinue).GetValue("")
                if ($installPath) {
                    $r = Test-PyExe (Join-Path $installPath "python.exe")
                    if ($r) { return $r }
                }
            } catch {}
        }
    }

    # 4. 掃常見安裝目錄 ---------------------------------------------------
    $bases = @($env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)}) | Where-Object { $_ }
    $globs = @()
    foreach ($b in $bases) {
        $globs += (Join-Path $b "Programs\Python\Python3*\python.exe")
        $globs += (Join-Path $b "Python3*\python.exe")
    }
    $globs += "C:\Python3*\python.exe"
    foreach ($g in $globs) {
        foreach ($hit in (Get-ChildItem -Path $g -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) {
            $r = Test-PyExe $hit.FullName
            if ($r) { return $r }
        }
    }

    return $null
}

function Invoke-Py {
    param([string[]]$PyArgs)
    & $script:PY.Exe @($script:PY.Args + $PyArgs)
}

function Get-PortOwners {
    $ids = @()
    try {
        $ids += (Get-NetTCPConnection -LocalPort $PORT -State Listen -ErrorAction SilentlyContinue).OwningProcess
    } catch {}
    return $ids | Where-Object { $_ } | Select-Object -Unique
}

function Stop-Service-OnPort {
    foreach ($procId in Get-PortOwners) {
        try { Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Milliseconds 800
}

# ── 啟動前檢查 ───────────────────────────────────────────────────────────
# 把「一定會失敗」的情況先擋下來並講清楚原因，而不是讓伺服器在另一個視窗
# 閃一下就消失、主視窗還印一句沒用的「已啟動」。
function Test-Ready {
    if (-not (Test-Path (Join-Path $APPROOT "app\main.py"))) {
        Write-Head "啟動失敗：找不到程式"
        Write-Host "  在這兩個位置都找不到 app\main.py：" -ForegroundColor Yellow
        Write-Host "    $HERE"
        Write-Host "    $(Split-Path -Parent $HERE)"
        Write-Host ""
        Write-Host "  正常情況你不會看到這個畫面。可能原因："
        Write-Host "    - 只複製了 service.bat，沒把旁邊的 app 資料夾一起複製。"
        Write-Host "    - 從 GitHub 下載後，把 service.bat 搬離了 notebook-package 資料夾。"
        Write-Host ""
        Write-Host "  最簡單的解法：用維護人員寄的『完整包』zip，整包解壓後直接雙擊"
        Write-Host "  裡面的 service.bat，不要單獨搬動任何檔案。"
        return $false
    }

    # openpyxl 一起檢查：它是 Excel 匯入匯出的執行時相依，但寫成函式內 import，
    # 少了它系統照常啟動，要等使用者真的按下匯入才會炸。在這裡一起擋，
    # 才不會讓人以為系統是好的、用到一半才發現壞掉。
    Invoke-Py @("-c", "import fastapi, uvicorn, openpyxl") 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Head "缺少必要套件（fastapi / uvicorn / openpyxl）"
        Write-Host "  這台電腦有 Python，但還沒安裝本系統需要的套件。" -ForegroundColor Yellow
        Write-Host ""
        $ans = Read-Host "  現在要自動安裝嗎？（Y=安裝 / 其他=取消）"
        if ($ans -notmatch '^[Yy]') { Write-Host "  已取消。"; return $false }

        Write-Host ""
        Write-Host "  安裝中，請稍候..."
        # 只裝執行時要的三個套件，不裝 pytest / httpx / playwright。
        # 部署端不跑測試（選單裡也沒有這個功能），而 playwright 裝完還會再去抓
        # 瀏覽器二進位檔，在連不到外網的公司網路幾乎必敗——為了跑一個 Web 服務
        # 去裝它，等於平白多一個失敗點。
        Invoke-Py @("-m", "pip", "install", "-r", (Join-Path $APPROOT "requirements-runtime.txt"))
        Invoke-Py @("-c", "import fastapi, uvicorn, openpyxl") 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "  安裝後仍然找不到套件。" -ForegroundColor Red
            Write-Host "  可能是沒有網路，或公司網路擋住了 pip。"
            Write-Host "  請用選項 6 產生診斷報告，交給維護人員。"
            return $false
        }
        Write-Host "  安裝完成。" -ForegroundColor Green
    }

    # 沒有 .env 就自動建一份。否則帳號密碼讀不到，畫面會變成「怎麼登入都說密碼錯」。
    # 放在 $APPROOT（app\ 的上一層）：app/main.py 是從那裡讀 .env 的，兩者必須一致。
    $envFile = Join-Path $APPROOT ".env"
    if (-not (Test-Path $envFile)) {
        Write-Host ""
        Write-Host "  找不到 .env 設定檔，自動建立一份試辦用的（免密碼登入）。" -ForegroundColor Yellow
        Write-Host "  正式使用前請把 PILOT_PASSWORDLESS 改成 0，並設定各自的密碼。"
        $rnd = -join ((1..48) | ForEach-Object { "{0:x}" -f (Get-Random -Max 16) })
        @(
            "SESSION_SECRET=$rnd"
            "AP01_PASSWORD=1qaz@WSX"
            "AP02_PASSWORD=1qaz@WSX"
            "AP03_PASSWORD=1qaz@WSX"
            "AP04_PASSWORD=1qaz@WSX"
            "ADMIN_PASSWORD=1qaz@WSX"
            "PILOT_PASSWORDLESS=1"
        ) | Set-Content -Path $envFile -Encoding utf8
    }
    return $true
}

# ── 啟動並驗證 ───────────────────────────────────────────────────────────
# 啟動後真的去打 /health 確認活著。沒活就把紀錄檔最後幾行印出來，
# 不讓錯誤訊息跟著另一個視窗一起消失。
function Start-Service-Now {
    if (-not (Test-Ready)) { Pause-Back; return }

    if ((Get-PortOwners).Count -gt 0) {
        Write-Host "  連接埠 $PORT 已有程式在使用，先停掉舊的。"
        Stop-Service-OnPort
    }

    Add-Content -Path $LOGFILE -Value "---- 啟動 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ----" -Encoding utf8
    $pyCmd = ($PY.Exe + " " + ($PY.Args -join " ")).Trim()
    # 不用 Tee-Object：PowerShell 5.1 的 Tee-Object 沒有 -Encoding，一律寫 UTF-16LE，
    # 但同一個檔的表頭是 Add-Content 寫的單位元組文字。兩種編碼混在一份 log 裡，
    # 診斷報告讀出來會變成「每個字元中間夾一個空白」——而那段正是最需要看的錯誤訊息。
    # 改用 ForEach-Object 手動轉發：畫面照樣有輸出，寫檔則跟其他地方統一走 utf8。
    $inner = "$pyCmd -m uvicorn app.main:app --host 127.0.0.1 --port $PORT 2>&1 | " +
             "ForEach-Object { `$_; Add-Content -Path '$LOGFILE' -Value `$_ -Encoding utf8 }"
    Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile", "-Command", $inner) `
                  -WorkingDirectory $APPROOT -WindowStyle Hidden | Out-Null

    Write-Host "  啟動中，正在確認服務是否正常回應..."
    $ok = $false
    for ($i = 0; $i -lt 25; $i++) {
        Start-Sleep -Seconds 1
        try {
            if ((Invoke-WebRequest "http://127.0.0.1:$PORT/health" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) {
                $ok = $true; break
            }
        } catch {}
    }

    if ($ok) {
        Write-Host ""
        Write-Host "  啟動成功，服務正常回應。" -ForegroundColor Green
        Start-Process "http://127.0.0.1:$PORT"
        Write-Host "  瀏覽器已開啟 http://127.0.0.1:$PORT"
        Pause-Back
        return
    }

    Write-Head "啟動失敗：服務沒有正常回應"
    Write-Host "  以下是紀錄檔最後 25 行，失敗原因通常就在裡面：" -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    if (Test-Path $LOGFILE) {
        Get-Content -Path $LOGFILE -Tail 25 -Encoding utf8
    } else {
        Write-Host "（沒有紀錄檔，代表 Python 連啟動都沒啟動起來）"
    }
    Write-Host ("-" * 60) -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  看不懂的話請用選項 6 產生診斷報告，把檔案傳給維護人員。"
    Pause-Back
}

# ── 診斷報告 ─────────────────────────────────────────────────────────────
# 把「維護人員一定會問的每件事」一次收集好，使用者只要傳一個檔案，
# 不必在電話裡逐項回答。
function New-DiagReport {
    $lines = @()
    $lines += "==== CL_FEE 診斷報告 ===="
    $lines += "產生時間: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $lines += "電腦名稱: $env:COMPUTERNAME"
    $lines += "使用者:   $env:USERNAME"
    $lines += "腳本位置: $HERE"
    $lines += "程式位置: $APPROOT$(if ($APPROOT -ne $HERE) { '  (在腳本上一層，判定為 GitHub clone 佈局)' })"
    $lines += "連接埠:   $PORT"
    $lines += "Windows:  $([System.Environment]::OSVersion.VersionString)"
    $lines += ""
    $lines += "---- Python ----"
    if ($PY) {
        $lines += "偵測到: $($PY.Exe) $($PY.Args -join ' ')  =>  $($PY.Version)"
    } else {
        $lines += "偵測到: 無（PATH / 登錄檔 / 常見目錄 / python_path.txt 都找不到可用的 Python 3）"
    }
    foreach ($probe in @("py -3 --version", "python --version", "where python")) {
        $lines += ""
        $lines += "> $probe"
        try { $lines += (cmd /c "$probe 2>&1") } catch { $lines += "（執行失敗）" }
    }
    # 登錄檔登記的 Python：安裝程式會寫 InstallPath，即使沒進 PATH 也查得到。
    # 若這裡列得出來、但上面偵測卻是「無」，代表 python.exe 檔案不在登記的位置了。
    $lines += ""
    $lines += "> Windows 登錄檔登記的 Python"
    $regHits = @()
    foreach ($hive in @("HKLM:\SOFTWARE\Python\PythonCore", "HKCU:\SOFTWARE\Python\PythonCore", "HKLM:\SOFTWARE\WOW6432Node\Python\PythonCore")) {
        if (-not (Test-Path $hive)) { continue }
        foreach ($ver in (Get-ChildItem $hive -ErrorAction SilentlyContinue)) {
            try {
                $ip = (Get-Item -LiteralPath (Join-Path $ver.PSPath "InstallPath") -ErrorAction SilentlyContinue).GetValue("")
                if ($ip) { $regHits += ("  {0}  =>  {1}" -f $ver.PSChildName, (Join-Path $ip "python.exe")) }
            } catch {}
        }
    }
    if ($regHits.Count -gt 0) { $lines += $regHits } else { $lines += "  （登錄檔沒有登記任何 Python）" }
    $ptxtPath = Join-Path $HERE "python_path.txt"
    $lines += ""
    $lines += "> 手動指定檔 python_path.txt: $(if (Test-Path $ptxtPath) { '有' } else { '無' })"
    $lines += ""
    $lines += "---- 套件 ----"
    if ($PY) {
        try {
            $lines += (Invoke-Py @("-c", "import fastapi, uvicorn, openpyxl, sys; print('python', sys.version); print('fastapi', fastapi.__version__); print('uvicorn', uvicorn.__version__); print('openpyxl', openpyxl.__version__)") 2>&1)
        } catch { $lines += "（無法載入 fastapi / uvicorn / openpyxl）" }
    }
    # 這一段是為了「一趟 mail 問完」而存在的。維護端拿不到這台機器，每問一件事就是
    # 一趟來回、好幾天。所以要一次收齊「下一步該送什麼」需要的全部資訊：
    #   - wheel 標籤：離線輪子是綁 Python 版本與平台的，cp311 跟 cp313 不通用。
    #     沒有這行就沒辦法先打好離線包，只能再問一次。
    #   - PyPI 通不通：決定「叫他按 Y 自動安裝」還是「改送離線輪子」。
    #   - Proxy：公司網路多半要走 proxy，pip 沒設就是連不出去，但錯誤訊息看起來
    #     跟「完全沒網路」一模一樣。
    $lines += ""
    $lines += "---- 安裝環境（決定下一步要送什麼）----"
    if ($PY) {
        try {
            $lines += (Invoke-Py @("-c", "import sys, sysconfig; print('python 版本:', '.'.join(map(str, sys.version_info[:3]))); print('平台:', sysconfig.get_platform()); print('wheel 標籤: cp%d%d-%s' % (sys.version_info[0], sys.version_info[1], sysconfig.get_platform().replace('-','_').replace('.','_')))") 2>&1)
        } catch { $lines += "（無法取得平台資訊）" }
        try {
            $lines += ("pip: " + (Invoke-Py @("-m", "pip", "--version") 2>&1))
        } catch { $lines += "pip: （無法執行，可能沒裝 pip）" }
    }
    foreach ($v in @("HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")) {
        $val = [Environment]::GetEnvironmentVariable($v)
        if ($val) { $lines += ("{0}: {1}" -f $v, $val) } else { $lines += ("{0}: （未設定）" -f $v) }
    }
    try {
        $sysProxy = ([System.Net.WebRequest]::GetSystemWebProxy()).GetProxy("https://pypi.org")
        $lines += ("系統 Proxy 設定: " + $sysProxy.AbsoluteUri)
    } catch { $lines += "系統 Proxy 設定: （讀不到）" }

    $lines += ""
    $lines += "---- 網路連通性 ----"
    foreach ($probe in @(
        @{ Name = "PyPI（pip 抓套件的來源）"; Url = "https://pypi.org/simple/" },
        @{ Name = "GitHub（自動更新的來源）"; Url = "https://github.com" }
    )) {
        try {
            $resp = Invoke-WebRequest -Uri $probe.Url -Method Head -TimeoutSec 8 -UseBasicParsing -ErrorAction Stop
            $lines += ("{0,-26} 通（HTTP {1}）" -f $probe.Name, [int]$resp.StatusCode)
        } catch {
            $lines += ("{0,-26} 不通：{1}" -f $probe.Name, $_.Exception.Message)
        }
    }

    $lines += ""
    $lines += "---- 必要檔案 ----"
    foreach ($f in @("app\main.py", ".env", "requirements.txt", "requirements-runtime.txt", "data")) {
        $exists = Test-Path (Join-Path $APPROOT $f)
        $mark = "缺少"
        if ($exists) { $mark = "有" }
        $lines += ("{0,-20} {1}" -f $f, $mark)
    }
    $lines += ""
    $lines += "---- 連接埠占用 ----"
    try { $lines += (cmd /c "netstat -ano | findstr :$PORT 2>&1") } catch {}
    $lines += ""
    $lines += "---- 服務紀錄檔最後 60 行 ----"
    if (Test-Path $LOGFILE) { $lines += (Get-Content -Path $LOGFILE -Tail 60 -Encoding utf8) } else { $lines += "（沒有紀錄檔）" }

    $lines | Set-Content -Path $DIAGFILE -Encoding utf8
    Write-Host ""
    Write-Host "  診斷報告已產生：" -ForegroundColor Green
    Write-Host "    $DIAGFILE"
    Write-Host ""
    Write-Host "  請把這個檔案傳給維護人員。"
}

# ── 主流程 ───────────────────────────────────────────────────────────────
$PY = Find-Python
if (-not $PY) {
    Write-Head "啟動失敗：這台電腦找不到可以用的 Python 3"
    Write-Host "  已嘗試 py -3 / python / python3，三個都不能執行。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  常見原因："
    Write-Host "    1. 這台電腦沒有安裝 Python。"
    Write-Host "    2. 有安裝，但安裝時沒勾選「Add Python to PATH」。"
    Write-Host "    3. 「python」指到微軟商店的空殼程式（打 python 會跳出商店）。"
    Write-Host ""
    Write-Host "  怎麼處理（兩個都做最保險）："
    Write-Host ""
    Write-Host "  [A] 先關掉微軟商店的假 python（如果上面第 3 點是你的狀況，這步最快）："
    Write-Host "      設定 → 應用程式 → 應用程式執行別名 →"
    Write-Host "      把 python.exe 和 python3.exe 兩個開關「關閉」，然後重開這個視窗。"
    Write-Host ""
    Write-Host "  [B] 安裝真正的 Python："
    Write-Host "      到 https://www.python.org/downloads/ 安裝 Python 3.11 以上，"
    Write-Host "      安裝畫面第一頁務必勾選「Add python.exe to PATH」，裝完重開這個視窗。"
    Write-Host ""
    Write-Host "  [C] Python 已裝在指定路徑、但沒進 PATH（公司機器常見）："
    Write-Host "      本程式已自動找過 PATH、登錄檔、常見安裝目錄都沒找到。"
    Write-Host "      請在 service.bat 旁邊建一個檔案 python_path.txt，裡面只寫一行＝"
    Write-Host "      你的 python.exe 完整路徑，例如："
    Write-Host "          D:\Tools\Python312\python.exe"
    Write-Host "      存檔後重開這個視窗即可，不需要改任何其他設定。"
    Write-Host ""
    Write-Host "  怎麼確認好了：重開視窗，選單頂端若印出 Python 版本就成功。"
    Write-Host ""
    New-DiagReport
    Write-Host ""
    Write-Host "  按 Enter 結束..." -ForegroundColor DarkGray
    [void](Read-Host)
    exit 1
}

while ($true) {
    Clear-Host
    Write-Host "============================================"
    Write-Host "  CL_FEE 服務控制台（連接埠 $PORT）"
    Write-Host "============================================"
    Write-Host ""
    Write-Host "   1. 啟動服務"
    Write-Host "   2. 停止服務"
    Write-Host "   3. 重新啟動服務"
    Write-Host "   4. 查看目前狀態"
    Write-Host "   5. 查看最近的紀錄（最後 50 行）"
    Write-Host "   6. 產生診斷報告（出問題時把這個檔傳給維護人員）"
    Write-Host "   0. 離開"
    Write-Host ""
    Write-Host "   Python：$($PY.Exe) $($PY.Args -join ' ')  ($($PY.Version))" -ForegroundColor DarkGray
    Write-Host "   紀錄檔：$LOGFILE" -ForegroundColor DarkGray
    Write-Host ""
    $choice = Read-Host "請輸入選項"

    switch ($choice) {
        "1" { Start-Service-Now }
        "2" {
            Write-Host "  停止 $PORT 上的服務..."
            Add-Content -Path $LOGFILE -Value "---- 停止 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ----" -Encoding utf8
            Stop-Service-OnPort
            Write-Host "  已停止。" -ForegroundColor Green
            Pause-Back
        }
        "3" {
            Add-Content -Path $LOGFILE -Value "---- 重新啟動 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ----" -Encoding utf8
            Stop-Service-OnPort
            Start-Service-Now
        }
        "4" {
            Write-Host ""
            $owners = Get-PortOwners
            if ($owners.Count -gt 0) {
                foreach ($o in $owners) { Write-Host "  服務執行中，連接埠 $PORT（處理程序編號 $o）" -ForegroundColor Green }
                try {
                    $h = Invoke-RestMethod "http://127.0.0.1:$PORT/health" -TimeoutSec 3
                    Write-Host "  版本：$($h.build)"
                } catch { Write-Host "  但 /health 沒有回應，服務可能卡住了。" -ForegroundColor Yellow }
            } else {
                Write-Host "  服務目前沒有在執行（連接埠 $PORT 沒有程式在監聽）。"
            }
            Pause-Back
        }
        "5" {
            Write-Host ""
            if (Test-Path $LOGFILE) { Get-Content -Path $LOGFILE -Tail 50 -Encoding utf8 } else { Write-Host "  還沒有紀錄檔，請先啟動一次服務。" }
            Pause-Back
        }
        "6" { New-DiagReport; Pause-Back }
        "0" { exit 0 }
    }
}
