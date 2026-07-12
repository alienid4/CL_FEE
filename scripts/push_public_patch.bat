@echo off
setlocal

set "SRC=%~dp0.."
set "DEST=C:\Users\User\Desktop\CL_FEE_public_repo"

echo ============================================
echo   Push code patch to public GitHub repo
echo ============================================
echo.

if not exist "%DEST%" (
    echo First time setup: cloning public repo...
    git clone https://github.com/alienid4/CL_FEE.git "%DEST%"
    if errorlevel 1 (
        echo Clone failed. Check your network / git setup.
        pause
        exit /b 1
    )
)

echo Copying latest app/ and tests/ into the public repo folder...
robocopy "%SRC%\app" "%DEST%\app" /MIR /NFL /NDL /NJH /NJS >nul
robocopy "%SRC%\tests" "%DEST%\tests" /MIR /NFL /NDL /NJH /NJS >nul
copy /Y "%SRC%\requirements.txt" "%DEST%\requirements.txt" >nul
copy /Y "%SRC%\pytest.ini" "%DEST%\pytest.ini" >nul

cd /d "%DEST%"
git add -A
git commit -m "patch update"
git push

echo.
echo Done. Press any key to close.
pause
