@echo off
setlocal

rem Start both local services after replacing anything using their ports.
cd /d "%~dp0"

echo Stopping processes listening on ports 8000, 8001, and 8002...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports = 8000,8001,8002; Get-NetTCPConnection -State Listen -LocalPort $ports -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"

echo Starting backend on http://127.0.0.1:8000...
start "EducAgent Server :8000" /D "%~dp0" cmd /k "set PYTHONPATH=src&& conda run --no-capture-output -n educagent-sdk python examples\playable_demo.py --port 8000"

echo Starting frontend on http://127.0.0.1:8002...
start "EducAgent Client :8002" /D "%~dp0" cmd /k "npm run web:dev -- --host 127.0.0.1 --port 8002 --strictPort"

timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8002"
endlocal
