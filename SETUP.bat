@echo off
title 🔧 FILE PROTECTOR - SETUP
color 0B

echo.
echo ========================================
echo    🔧 FILE PROTECTOR - INITIAL SETUP
echo ========================================
echo.
echo This will protect a folder with encryption
echo.

:: Ask for folder name
set /p FOLDER_NAME="📁 Enter folder name to protect: "

if "%FOLDER_NAME%"=="" (
    echo ❌ No folder name entered!
    pause
    exit
)

echo.
echo 🔐 Creating protection for: %FOLDER_NAME%
echo.

:: Check if folder exists
if not exist "%FOLDER_NAME%" (
    echo 📁 Creating folder: %FOLDER_NAME%
    mkdir "%FOLDER_NAME%"
)

:: Run initialization
python protector.py "%FOLDER_NAME%" init

echo.
echo ========================================
echo    ✅ SETUP COMPLETE!
echo ========================================
echo.
echo 📁 Protected folder: %FOLDER_NAME%
echo 🔑 Remember your password!
echo.
echo 💡 Use UNLOCK.bat to access your files
echo 💡 Use LOCK.bat to secure them
echo.

pause