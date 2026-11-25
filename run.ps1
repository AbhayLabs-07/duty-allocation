Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting Smart Exam Duty Fairness System (Kam Bato)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Starting Backend API (FastAPI on Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', '$env:PYTHONPATH="backend"; .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload'

Write-Host "[2/2] Starting Frontend UI (Next.js on Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'npm run dev'

Write-Host "`n========================================================" -ForegroundColor Cyan
Write-Host " System is running!" -ForegroundColor Green
Write-Host " - Frontend Web UI:  http://localhost:3000" -ForegroundColor White
Write-Host " - Backend API Docs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "========================================================" -ForegroundColor Cyan
