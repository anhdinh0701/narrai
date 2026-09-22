@echo off
title NarrAI - Ket noi ComfyUI qua ngrok
color 0B
echo ================================================================
echo             KET NOI COMFYUI VOI NGROK (CHO NARRAI)
echo ================================================================
echo.

:: 1. Kiem tra xem ComfyUI co dang chay tren cong 8188 khong
echo [*] Dang kiem tra ComfyUI tren cong 8188...
netstat -ano | findstr ":8188" | findstr "LISTENING" >nul
if %ERRORLEVEL% equ 0 (
    echo [OK] ComfyUI dang chay tren cong 8188!
) else (
    echo [CANH BAO] Khong thay ComfyUI dang chay tren cong 8188.
    echo          Vui long khoi dong ComfyUI tren may cua ban truoc!
    echo.
)

:: 2. Kiem tra ngrok
echo [*] Dang kiem tra ngrok...
where ngrok >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [LOI] Khong tim thay lenh ngrok trong he thong!
    echo       Hay cai ngrok hoac tai tu https://ngrok.com/download
    pause
    exit /b 1
)

echo.
echo ================================================================
echo HUONG DAN SU DUNG:
echo 1. Cua so ngrok se mo ra. Hay tim dong:
echo      Forwarding                    https://xxxx-xxxx.ngrok-free.app -> http://localhost:8188
echo 2. Copy duong link https://xxxx-xxxx.ngrok-free.app do.
echo 3. Neu chay online tren Render:
echo      Vao Render Dashboard -> Environment -> Sua COMFYUI_URL = duong link vua copy.
echo 4. Neu chay backend local:
echo      Vao file backend\.env -> them/sua dong:
echo      COMFYUI_URL=duong link vua copy
echo ================================================================
echo.
echo [*] Dang khoi dong tunnel ngrok toi http://127.0.0.1:8188...
echo.

ngrok http 8188 --host-header="localhost:8188"

pause
