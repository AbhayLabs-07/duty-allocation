@echo off
title Kam Bato Algorithm - Launcher
echo ========================================================
echo  Starting Smart Exam Duty Fairness System (Kam Bato)
echo ========================================================
echo.

echo [1/2] Starting Backend API (FastAPI on Port 8000)...
start "Kam Bato - Backend API" cmd /k "set PYTHONPATH=backend && .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Starting Frontend UI (Next.js on Port 3000)...
start "Kam Bato - Frontend UI" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo  System is starting!
echo  - Frontend Web UI:  http://localhost:3000
echo  - Backend API Docs: http://127.0.0.1:8000/docs
echo ========================================================
pause
