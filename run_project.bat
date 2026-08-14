@echo off
title Resume CMS - Startup Launcher
echo ==========================================================
echo       Resume CMS ^& Static Portfolio Startup Launcher
echo ==========================================================
echo.

echo [1/2] Starting Backend API Server (FastAPI)...
start "Backend Server (FastAPI)" cmd /k "cd backend && call venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Frontend Client (Next.js)...
start "Frontend Client (Next.js)" cmd /k "cd /d frontend && npm run dev"

echo.
echo ==========================================================
echo  SUCCESS: Both systems launched in separate windows!
echo ==========================================================
echo  - Backend API running at: http://127.0.0.1:8000/docs
echo  - Frontend Dashboard running at: http://localhost:3000
echo.
echo  To shut down, simply close the opened terminal windows.
echo ==========================================================
echo.
pause
