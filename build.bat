@echo off
rem Build Sclayka into a single exe: dist\Sclayka.exe
cd /d "%~dp0"
if not exist .venv (
    python -m venv .venv
    .venv\Scripts\python -m pip install -r requirements.txt pyinstaller
)
.venv\Scripts\pyinstaller --noconfirm --onefile --windowed --name Sclayka --icon icon.ico ^
    --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtQml ^
    --exclude-module PySide6.QtQuick --exclude-module PySide6.QtNetwork ^
    --exclude-module PySide6.QtPdf --exclude-module PySide6.Qt3DCore ^
    --exclude-module tkinter ^
    sclayka.py
