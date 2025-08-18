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

Write-Log "Iniciando monitoreo programado de indicadores..."
Write-Log "Directorio base: $base"
Write-Log "Python: $py"
Write-Log "Log file: $logFile"

try {
    Write-Log "Ejecutando BTC/USD..."
    $result = & $py "$base\main.py" --symbol "BTC/USD" --json
    if ($LASTEXITCODE -eq 0) {
        Write-Log "BTC/USD completado exitosamente"
        Write-Log "Resultado: $result"
    } else {
        Write-Log "Error en BTC/USD (Exit Code: $LASTEXITCODE)"
    }
    
    Start-Sleep -Seconds 150
    
    Write-Log "Ejecutando ETH/USD..."
    $result = & $py "$base\main.py" --symbol "ETH/USD" --json
    if ($LASTEXITCODE -eq 0) {
        Write-Log "ETH/USD completado exitosamente"
        Write-Log "Resultado: $result"
    } else {
        Write-Log "Error en ETH/USD (Exit Code: $LASTEXITCODE)"
    }
    
    Start-Sleep -Seconds 150
    
    Write-Log "Ejecutando BNB/USD..."
    $result = & $py "$base\main.py" --symbol "BNB/USD" --json
    if ($LASTEXITCODE -eq 0) {
        Write-Log "BNB/USD completado exitosamente"
        Write-Log "Resultado: $result"
    } else {
        Write-Log "Error en BNB/USD (Exit Code: $LASTEXITCODE)"
    }
    
    Write-Log "Todos los simbolos procesados!"
    
} catch {
    Write-Log "Error en PowerShell: $_"
    Write-Log "Error completo: $($_.Exception.Message)"
}

Write-Log "Tarea programada completada"
