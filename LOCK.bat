@echo off
title 🔒 FILE PROTECTOR - LOCK
color 0C

echo.
echo ========================================
echo    🔒 FILE PROTECTOR - LOCK FILES
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
echo 🔒 Locking: %FOLDER_NAME%
echo.

python protector.py "%FOLDER_NAME%" protect

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo    ✅ FILES LOCKED!
    echo ========================================
    echo.
    echo 📁 Folder is now HIDDEN
    echo 🔒 All files encrypted
    echo.
) else (
    echo.
    echo ❌ Lock failed!
    echo.
)

pause