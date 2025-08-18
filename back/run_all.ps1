$ErrorActionPreference = "Stop"
$base = "D:\Indicadores"
$py   = "C:/Users/lucia/AppData/Local/Programs/Python/Python313/python.exe"

Write-Host "🚀 Iniciando monitoreo de múltiples símbolos..." -ForegroundColor Green
Write-Host "📍 Directorio base: $base" -ForegroundColor Yellow
Write-Host "🐍 Python: $py" -ForegroundColor Yellow
Write-Host ""

Write-Host "📊 Ejecutando BTC/USD..." -ForegroundColor Cyan
& $py "$base\main.py" --symbol "BTC/USD"
Write-Host "✅ BTC/USD completado" -ForegroundColor Green
Write-Host "⏳ Esperando 5 minutos..." -ForegroundColor Yellow
Start-Sleep -Seconds 150

Write-Host "📊 Ejecutando ETH/USD..." -ForegroundColor Cyan
& $py "$base\main.py" --symbol "ETH/USD"
Write-Host "✅ ETH/USD completado" -ForegroundColor Green
Write-Host "⏳ Esperando 5 minutos..." -ForegroundColor Yellow
Start-Sleep -Seconds 150

Write-Host "📊 Ejecutando BNB/USD..." -ForegroundColor Cyan
& $py "$base\main.py" --symbol "BNB/USD"
Write-Host "✅ BNB/USD completado" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Todos los símbolos procesados exitosamente!" -ForegroundColor Green

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
