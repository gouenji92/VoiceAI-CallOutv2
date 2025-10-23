# Script khởi động server VoiceAI
# Tự động kiểm tra và khởi động nếu chưa chạy

Write-Host "🚀 VOICEAI - AUTO STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Kiểm tra port 8000
$port = 8000
$portCheck = netstat -ano | findstr ":$port"

if ($portCheck) {
    Write-Host "✅ Server đã chạy trên port $port" -ForegroundColor Green
    Write-Host ""
    Write-Host "Để test, chạy trong terminal mới:" -ForegroundColor Yellow
    Write-Host "  python test_full_system.py" -ForegroundColor White
    exit 0
}

Write-Host "⚠️  Server chưa chạy, đang khởi động..." -ForegroundColor Yellow
Write-Host ""

# Kích hoạt virtual environment (nếu có)
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "📦 Kích hoạt virtual environment..." -ForegroundColor Cyan
    & .venv\Scripts\Activate.ps1
}

# Khởi động server
Write-Host "🔥 Khởi động FastAPI server..." -ForegroundColor Green
Write-Host ""
Write-Host "Để test:" -ForegroundColor Yellow
Write-Host "  1. Mở terminal mới (Ctrl+Shift+``)" -ForegroundColor White
Write-Host "  2. Chạy: python test_full_system.py" -ForegroundColor White
Write-Host ""
Write-Host "Để dừng server: Ctrl+C" -ForegroundColor Red
Write-Host ""

python -X utf8 -m uvicorn app.main:app --reload
