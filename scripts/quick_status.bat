@echo off
chcp 65001 >nul
python check_progress.py
timeout /t 5 >nul
goto :eof
