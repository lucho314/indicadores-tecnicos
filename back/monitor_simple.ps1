$base = "D:\Indicadores"
$logFile = "$base\logs\scheduled_task.log"

Write-Host "MONITOR DE TAREA PROGRAMADA" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green
Write-Host "Directorio: $base" -ForegroundColor Yellow
Write-Host "Log file: $logFile" -ForegroundColor Yellow
Write-Host ""

# Verificar estado de la tarea
try {
    $task = Get-ScheduledTask -TaskName "Indicadores_4h" -ErrorAction Stop
    $taskInfo = Get-ScheduledTaskInfo -TaskName "Indicadores_4h"
    
    Write-Host "ESTADO DE LA TAREA:" -ForegroundColor Cyan
    Write-Host "Estado: $($task.State)" -ForegroundColor White
    Write-Host "Ultima ejecucion: $($taskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "Proxima ejecucion: $($taskInfo.NextRunTime)" -ForegroundColor White
    Write-Host "Ultimo resultado: $($taskInfo.LastTaskResult)" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "No se pudo obtener informacion de la tarea: $_" -ForegroundColor Red
    Write-Host ""
}

# Mostrar últimas líneas del log
if (Test-Path $logFile) {
    Write-Host "ULTIMAS 10 LINEAS DEL LOG:" -ForegroundColor Cyan
    Write-Host "-"*50 -ForegroundColor Gray
    
    $lastLines = Get-Content $logFile -Tail 10
    foreach ($line in $lastLines) {
        if ($line -match "Error|ERROR") {
            Write-Host $line -ForegroundColor Red
        } elseif ($line -match "completado|exitosamente|SUCCESS") {
            Write-Host $line -ForegroundColor Green
        } elseif ($line -match "Ejecutando|EJECUTANDO") {
            Write-Host $line -ForegroundColor Cyan
        } else {
            Write-Host $line -ForegroundColor White
        }
    }
    
    Write-Host "-"*50 -ForegroundColor Gray
    Write-Host ""
    
    # Mostrar tamaño del archivo de log
    $logSize = (Get-Item $logFile).Length
    Write-Host "Tamano del log: $([math]::Round($logSize/1KB, 2)) KB" -ForegroundColor Yellow
    
} else {
    Write-Host "Archivo de log no encontrado: $logFile" -ForegroundColor Red
}

Write-Host ""
Write-Host "OPCIONES:" -ForegroundColor Green
Write-Host "1. Ejecutar tarea manualmente" -ForegroundColor White
Write-Host "2. Ver log completo" -ForegroundColor White
Write-Host "3. Ejecutar script directamente" -ForegroundColor White
Write-Host "4. Salir" -ForegroundColor White

$choice = Read-Host "`nSelecciona una opcion (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Ejecutando tarea manualmente..." -ForegroundColor Cyan
        schtasks /run /tn "Indicadores_4h"
    }
    "2" {
        if (Test-Path $logFile) {
            Write-Host "`nLOG COMPLETO:" -ForegroundColor Cyan
            Get-Content $logFile
        } else {
            Write-Host "No hay archivo de log" -ForegroundColor Red
        }
    }
    "3" {
        Write-Host "Ejecutando script directamente..." -ForegroundColor Cyan
        & "D:\Indicadores\run_scheduled.ps1"
    }
    "4" {
        Write-Host "Hasta luego!" -ForegroundColor Green
    }
}
