@echo off
rem Build the installer: dist\Sclayka-setup-<version>.exe
rem Needs Inno Setup 6: https://jrsoftware.org/isdl.php
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt pyinstaller
)
.venv\Scripts\pyinstaller --noconfirm --onedir --windowed --name Sclayka --icon icon.ico ^
    --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtQml ^
    --exclude-module PySide6.QtQuick --exclude-module PySide6.QtNetwork ^
    --exclude-module PySide6.QtPdf --exclude-module PySide6.Qt3DCore ^
    --exclude-module tkinter ^
    sclayka.py || exit /b 1

set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" (
    echo Inno Setup 6 not found
    exit /b 1
)
"%ISCC%" installer.iss
