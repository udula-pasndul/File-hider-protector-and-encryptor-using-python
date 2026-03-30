@echo off
title 🔓 FILE PROTECTOR - UNLOCK
color 0A

echo.
echo ========================================
echo    🔓 FILE PROTECTOR - UNLOCK FILES
echo ========================================
echo.

:: Ask for folder name
set /p FOLDER_NAME="📁 Enter your protected folder name: "

if "%FOLDER_NAME%"=="" (
    echo ❌ No folder name entered!
    pause
    exit
)

:: Check if folder exists
if not exist "%FOLDER_NAME%" (
    echo ❌ Folder '%FOLDER_NAME%' not found!
    echo.
    echo 💡 Make sure the folder name is correct
    pause
    exit
)

echo.
echo 🔓 Unlocking: %FOLDER_NAME%
echo.

:: Unlock files
python protector.py "%FOLDER_NAME%" restore

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    ✅ FILES UNLOCKED!
    echo ========================================
    echo.
    echo 📂 Folder will open automatically
    echo 🔒 Files will auto-lock after 5 minutes
    echo.
    echo 💡 Close this window to lock immediately
    echo ========================================
    echo.
    
    :: Auto-lock after 5 minutes (300 seconds)
    timeout /t 300 /nobreak >nul
    
    echo.
    echo 🔒 Auto-locking files...
    python protector.py "%FOLDER_NAME%" protect
    
    echo.
    echo ========================================
    echo    🔒 FILES LOCKED AGAIN!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo    ❌ UNLOCK FAILED!
    echo ========================================
    echo.
    echo 💡 Check your password and try again
)

pause