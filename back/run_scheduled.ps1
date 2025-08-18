$ErrorActionPreference = "Stop"
$base = "D:\Indicadores"
$py   = "C:/Users/lucia/AppData/Local/Programs/Python/Python313/python.exe"
$logFile = "$base\logs\scheduled_task.log"

# Crear directorio de logs si no existe
$logDir = Split-Path $logFile -Parent
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force
}

function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Add-Content -Path $logFile -Value $logMessage
    Write-Host $logMessage
}

Write-Log "🚀 Iniciando monitoreo programado de indicadores..."
Write-Log "📍 Directorio base: $base"
Write-Log "🐍 Python: $py"
Write-Log "📝 Log file: $logFile"

try {
    Write-Log "📊 Ejecutando BTC/USD..."
    $btcOutput = & $py "$base\main.py" --symbol "BTC/USD" --json 2>&1
    Write-Log "✅ BTC/USD completado"
    Write-Log "Resultado BTC/USD: $btcOutput"
    
    Start-Sleep -Seconds 10  # Pausa corta entre símbolos
    
    Write-Log "📊 Ejecutando ETH/USD..."
    $ethOutput = & $py "$base\main.py" --symbol "ETH/USD" --json 2>&1
    Write-Log "✅ ETH/USD completado"
    Write-Log "Resultado ETH/USD: $ethOutput"
    
    Start-Sleep -Seconds 10
    
    Write-Log "📊 Ejecutando BNB/USD..."
    $bnbOutput = & $py "$base\main.py" --symbol "BNB/USD" --json 2>&1
    Write-Log "✅ BNB/USD completado"
    Write-Log "Resultado BNB/USD: $bnbOutput"
    
    Write-Log "🎉 Todos los símbolos procesados exitosamente!"
    
} catch {
    Write-Log "❌ Error: $_"
    Write-Log "❌ Error completo: $($_.Exception.Message)"
    Write-Log "❌ Stack trace: $($_.ScriptStackTrace)"
}

Write-Log "📄 Tarea programada completada"
