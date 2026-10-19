@echo off
chcp 65001 > nul
echo ==========================================
echo  正在啟動 LINE Bot 伺服器...
echo ==========================================
call .\venv\Scripts\activate.bat
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
