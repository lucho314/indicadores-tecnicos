$base = "D:\Indicadores"
$logFile = "$base\logs\scheduled_task.log"

function Monitor-ScheduledTask {
    Write-Host "🔍 MONITOR DE TAREA PROGRAMADA" -ForegroundColor Green
    Write-Host "="*50 -ForegroundColor Green
    Write-Host "📍 Directorio: $base" -ForegroundColor Yellow
    Write-Host "📝 Log file: $logFile" -ForegroundColor Yellow
    Write-Host ""
    
    # Verificar estado de la tarea
    try {
        $task = Get-ScheduledTask -TaskName "Indicadores_4h_v2" -ErrorAction Stop
        $taskInfo = Get-ScheduledTaskInfo -TaskName "Indicadores_4h_v2"
        
        Write-Host "📋 ESTADO DE LA TAREA:" -ForegroundColor Cyan
        Write-Host "Estado: $($task.State)" -ForegroundColor White
        Write-Host "Última ejecución: $($taskInfo.LastRunTime)" -ForegroundColor White
        Write-Host "Próxima ejecución: $($taskInfo.NextRunTime)" -ForegroundColor White
        Write-Host "Último resultado: $($taskInfo.LastTaskResult)" -ForegroundColor White
        Write-Host ""
        
    } catch {
        Write-Host "❌ No se pudo obtener información de la tarea: $_" -ForegroundColor Red
        Write-Host ""
    }
    
    # Mostrar últimas líneas del log
    if (Test-Path $logFile) {
        Write-Host "📄 ÚLTIMAS 20 LÍNEAS DEL LOG:" -ForegroundColor Cyan
        Write-Host "-"*50 -ForegroundColor Gray
        
        $lastLines = Get-Content $logFile -Tail 20
        foreach ($line in $lastLines) {
            if ($line -match "Error|❌") {
                Write-Host $line -ForegroundColor Red
            } elseif ($line -match "completado|exitosamente|✅") {
                Write-Host $line -ForegroundColor Green
            } elseif ($line -match "Ejecutando|📊") {
                Write-Host $line -ForegroundColor Cyan
            } else {
                Write-Host $line -ForegroundColor White
            }
        }
        
        Write-Host "-"*50 -ForegroundColor Gray
        Write-Host ""
        
        # Mostrar tamaño del archivo de log
        $logSize = (Get-Item $logFile).Length
        Write-Host "📊 Tamaño del log: $([math]::Round($logSize/1KB, 2)) KB" -ForegroundColor Yellow
        
    } else {
        Write-Host "❌ Archivo de log no encontrado: $logFile" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🎛️ OPCIONES:" -ForegroundColor Green
    Write-Host "1. Ejecutar tarea manualmente" -ForegroundColor White
    Write-Host "2. Ver log completo" -ForegroundColor White
    Write-Host "3. Limpiar log" -ForegroundColor White
    Write-Host "4. Monitoreo en tiempo real" -ForegroundColor White
    Write-Host "5. Salir" -ForegroundColor White
    
    do {
        $choice = Read-Host "`nSelecciona una opción (1-5)"
        
        switch ($choice) {
            "1" {
                Write-Host "🏃 Ejecutando tarea manualmente..." -ForegroundColor Cyan
                try {
                    schtasks /run /tn "Indicadores_4h_v2"
                    Write-Host "✅ Tarea ejecutada. Revisa el log en unos momentos." -ForegroundColor Green
                } catch {
                    Write-Host "❌ Error ejecutando tarea: $_" -ForegroundColor Red
                }
            }
            "2" {
                if (Test-Path $logFile) {
                    Write-Host "`n📄 LOG COMPLETO:" -ForegroundColor Cyan
                    Write-Host "="*60 -ForegroundColor Gray
                    Get-Content $logFile | ForEach-Object {
                        if ($_ -match "Error|❌") {
                            Write-Host $_ -ForegroundColor Red
                        } elseif ($_ -match "completado|exitosamente|✅") {
                            Write-Host $_ -ForegroundColor Green
                        } else {
                            Write-Host $_ -ForegroundColor White
                        }
                    }
                    Write-Host "="*60 -ForegroundColor Gray
                } else {
                    Write-Host "❌ No hay archivo de log" -ForegroundColor Red
                }
            }
            "3" {
                if (Test-Path $logFile) {
                    Remove-Item $logFile -Force
                    Write-Host "✅ Log limpiado" -ForegroundColor Green
                } else {
                    Write-Host "❌ No hay archivo de log para limpiar" -ForegroundColor Red
                }
            }
            "4" {
                Write-Host "👁️ Monitoreo en tiempo real (Ctrl+C para salir)..." -ForegroundColor Cyan
                if (Test-Path $logFile) {
                    Get-Content $logFile -Wait -Tail 10
                } else {
                    Write-Host "❌ No hay archivo de log para monitorear" -ForegroundColor Red
                }
            }
            "5" {
                Write-Host "👋 ¡Hasta luego!" -ForegroundColor Green
                return
            }
            default {
                Write-Host "❌ Opción inválida" -ForegroundColor Red
            }
        }
    } while ($choice -ne "5")
}

Monitor-ScheduledTask
