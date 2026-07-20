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
$PORT     = 8888
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
function Find-Python {
    foreach ($cand in @(@{Exe="py"; Args=@("-3")}, @{Exe="python"; Args=@()}, @{Exe="python3"; Args=@()})) {
        try {
            $v = & $cand.Exe @($cand.Args + @("--version")) 2>$null
            if ($LASTEXITCODE -eq 0 -and $v -match "Python\s+3") {
                return [pscustomobject]@{ Exe = $cand.Exe; Args = $cand.Args; Version = "$v".Trim() }
            }
        } catch {}
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
    if (-not (Test-Path (Join-Path $HERE "app\main.py"))) {
        Write-Head "啟動失敗：資料夾不對"
        Write-Host "  在這個位置找不到 app\main.py：" -ForegroundColor Yellow
        Write-Host "    $HERE"
        Write-Host ""
        Write-Host "  service.bat 必須跟 app 資料夾放在一起。"
        Write-Host "  複製給別人時請整個 notebook-package 資料夾一起複製，不要只複製 .bat 檔。"
        return $false
    }

    Invoke-Py @("-c", "import fastapi, uvicorn") 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Head "缺少必要套件（fastapi / uvicorn）"
        Write-Host "  這台電腦有 Python，但還沒安裝本系統需要的套件。" -ForegroundColor Yellow
        Write-Host ""
        $ans = Read-Host "  現在要自動安裝嗎？（Y=安裝 / 其他=取消）"
        if ($ans -notmatch '^[Yy]') { Write-Host "  已取消。"; return $false }

        Write-Host ""
        Write-Host "  安裝中，請稍候..."
        Invoke-Py @("-m", "pip", "install", "-r", (Join-Path $HERE "requirements.txt"))
        Invoke-Py @("-c", "import fastapi, uvicorn") 2>$null | Out-Null
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
    $envFile = Join-Path $HERE ".env"
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

    Add-Content -Path $LOGFILE -Value "---- 啟動 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ----"
    $pyCmd = ($PY.Exe + " " + ($PY.Args -join " ")).Trim()
    $inner = "$pyCmd -m uvicorn app.main:app --host 127.0.0.1 --port $PORT 2>&1 | Tee-Object -FilePath '$LOGFILE' -Append"
    Start-Process -FilePath "powershell" -ArgumentList @("-NoProfile", "-Command", $inner) `
                  -WorkingDirectory $HERE -WindowStyle Hidden | Out-Null

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
        Get-Content -Path $LOGFILE -Tail 25
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
    $lines += "執行位置: $HERE"
    $lines += "連接埠:   $PORT"
    $lines += "Windows:  $([System.Environment]::OSVersion.VersionString)"
    $lines += ""
    $lines += "---- Python ----"
    if ($PY) {
        $lines += "偵測到: $($PY.Exe) $($PY.Args -join ' ')  =>  $($PY.Version)"
    } else {
        $lines += "偵測到: 無（py -3 / python / python3 都不能執行）"
    }
    foreach ($probe in @("py -3 --version", "python --version", "where python")) {
        $lines += ""
        $lines += "> $probe"
        try { $lines += (cmd /c "$probe 2>&1") } catch { $lines += "（執行失敗）" }
    }
    $lines += ""
    $lines += "---- 套件 ----"
    if ($PY) {
        try {
            $lines += (Invoke-Py @("-c", "import fastapi, uvicorn, sys; print('python', sys.version); print('fastapi', fastapi.__version__); print('uvicorn', uvicorn.__version__)") 2>&1)
        } catch { $lines += "（無法載入 fastapi / uvicorn）" }
    }
    $lines += ""
    $lines += "---- 必要檔案 ----"
    foreach ($f in @("app\main.py", ".env", "requirements.txt", "data")) {
        $exists = Test-Path (Join-Path $HERE $f)
        $mark = "缺少"
        if ($exists) { $mark = "有" }
        $lines += ("{0,-20} {1}" -f $f, $mark)
    }
    $lines += ""
    $lines += "---- 連接埠占用 ----"
    try { $lines += (cmd /c "netstat -ano | findstr :$PORT 2>&1") } catch {}
    $lines += ""
    $lines += "---- 服務紀錄檔最後 60 行 ----"
    if (Test-Path $LOGFILE) { $lines += (Get-Content -Path $LOGFILE -Tail 60) } else { $lines += "（沒有紀錄檔）" }

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
    Write-Host "  怎麼處理："
    Write-Host "    到 https://www.python.org/downloads/ 安裝 Python 3.11 以上，"
    Write-Host "    安裝畫面第一頁務必勾選「Add python.exe to PATH」，裝完重開這個視窗。"
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
            Add-Content -Path $LOGFILE -Value "---- 停止 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ----"
            Stop-Service-OnPort
            Write-Host "  已停止。" -ForegroundColor Green
            Pause-Back
        }
        "3" {
            Add-Content -Path $LOGFILE -Value "---- 重新啟動 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ----"
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
            if (Test-Path $LOGFILE) { Get-Content -Path $LOGFILE -Tail 50 } else { Write-Host "  還沒有紀錄檔，請先啟動一次服務。" }
            Pause-Back
        }
        "6" { New-DiagReport; Pause-Back }
        "0" { exit 0 }
    }
}
