@echo off
chcp 65001 > nul
echo ==========================================
echo  正在啟動 Cloudflare Tunnel 穿透...
echo  請將終端機中顯示的 https://xxx.trycloudflare.com
echo  加上 /callback 填入 LINE Developers 的 Webhook URL
echo ==========================================
if exist ".\cloudflared.exe" (
    .\cloudflared.exe tunnel --url http://localhost:8000
) else (
    cloudflared tunnel --url http://localhost:8000
)
pause
