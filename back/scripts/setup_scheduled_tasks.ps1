# Script de PowerShell para configurar tareas programadas en Windows
# para la expiración automática de estrategias de trading

param(
    [Parameter(Mandatory=$false)]
    [string]$Action = "install",
    
    [Parameter(Mandatory=$false)]
    [int]$IntervalMinutes = 10,
    
    [Parameter(Mandatory=$false)]
    [string]$ProjectPath = "D:\INDICADORES SW\back"
)

# Configuración
$TaskName = "ExpireTradingStrategies"
$TaskDescription = "Expira automáticamente estrategias de trading vencidas cada $IntervalMinutes minutos"
$ScriptPath = Join-Path $ProjectPath "scripts\expire_strategies.py"
$LogPath = Join-Path $ProjectPath "logs\expire_strategies.log"
$PythonExe = "python"

# Crear directorio de logs si no existe
$LogDir = Split-Path $LogPath -Parent
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    Write-Host "✅ Directorio de logs creado: $LogDir" -ForegroundColor Green
}

function Install-ScheduledTask {
    Write-Host "🔧 Instalando tarea programada: $TaskName" -ForegroundColor Yellow
    
    # Verificar que el script existe
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "❌ Error: Script no encontrado en $ScriptPath" -ForegroundColor Red
        exit 1
    }
    
    # Verificar que Python está disponible
    try {
        $pythonVersion = & $PythonExe --version 2>&1
        Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error: Python no encontrado. Asegúrate de que Python esté en el PATH" -ForegroundColor Red
        exit 1
    }
    
    # Eliminar tarea existente si existe
    try {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "🗑️ Tarea existente eliminada" -ForegroundColor Yellow
        }
    }
    catch {
        # Ignorar errores si la tarea no existe
    }
    
    # Crear acción de la tarea
    $Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "\"$ScriptPath\"" -WorkingDirectory $ProjectPath
    
    # Crear trigger (cada X minutos)
    $Trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365) -At (Get-Date)
    
    # Configuración de la tarea
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
    
    # Crear principal (ejecutar como usuario actual)
    $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
    
    # Registrar la tarea
    try {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $TaskDescription
        Write-Host "✅ Tarea programada '$TaskName' instalada exitosamente" -ForegroundColor Green
        Write-Host "   - Se ejecutará cada $IntervalMinutes minutos" -ForegroundColor Cyan
        Write-Host "   - Script: $ScriptPath" -ForegroundColor Cyan
        Write-Host "   - Logs: $LogPath" -ForegroundColor Cyan
        
        # Mostrar información de la tarea
        $task = Get-ScheduledTask -TaskName $TaskName
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        
        Write-Host "\n📋 Información de la tarea:" -ForegroundColor Yellow
        Write-Host "   Estado: $($task.State)" -ForegroundColor White
        Write-Host "   Última ejecución: $($taskInfo.LastRunTime)" -ForegroundColor White
        Write-Host "   Próxima ejecución: $($taskInfo.NextRunTime)" -ForegroundColor White
        
    }
    catch {
        Write-Host "❌ Error instalando tarea programada: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Uninstall-ScheduledTask {
    Write-Host "🗑️ Desinstalando tarea programada: $TaskName" -ForegroundColor Yellow
    
    try {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "✅ Tarea programada '$TaskName' eliminada exitosamente" -ForegroundColor Green
        }
        else {
            Write-Host "ℹ️ La tarea '$TaskName' no existe" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error eliminando tarea programada: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

function Show-TaskStatus {
    Write-Host "📋 Estado de la tarea programada: $TaskName" -ForegroundColor Yellow
    
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
            
            Write-Host "✅ Tarea encontrada" -ForegroundColor Green
            Write-Host "   Estado: $($task.State)" -ForegroundColor White
            Write-Host "   Descripción: $($task.Description)" -ForegroundColor White
            Write-Host "   Última ejecución: $($taskInfo.LastRunTime)" -ForegroundColor White
            Write-Host "   Próxima ejecución: $($taskInfo.NextRunTime)" -ForegroundColor White
            Write-Host "   Último resultado: $($taskInfo.LastTaskResult)" -ForegroundColor White
            
            # Mostrar triggers
            Write-Host "\n🔄 Triggers configurados:" -ForegroundColor Cyan
            foreach ($trigger in $task.Triggers) {
                if ($trigger.Repetition.Interval) {
                    Write-Host "   - Repetir cada: $($trigger.Repetition.Interval)" -ForegroundColor White
                }
            }
            
            # Verificar logs recientes
            if (Test-Path $LogPath) {
                $logSize = (Get-Item $LogPath).Length
                Write-Host "\n📄 Log file: $LogPath ($([math]::Round($logSize/1KB, 2)) KB)" -ForegroundColor Cyan
                
                # Mostrar últimas líneas del log
                $lastLines = Get-Content $LogPath -Tail 5 -ErrorAction SilentlyContinue
                if ($lastLines) {
                    Write-Host "   Últimas líneas:" -ForegroundColor Gray
                    foreach ($line in $lastLines) {
                        Write-Host "   $line" -ForegroundColor Gray
                    }
                }
            }
        }
        else {
            Write-Host "❌ Tarea '$TaskName' no encontrada" -ForegroundColor Red
            Write-Host "   Ejecuta: .\setup_scheduled_tasks.ps1 -Action install" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Error consultando tarea: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Test-ExpireScript {
    Write-Host "🧪 Probando script de expiración..." -ForegroundColor Yellow
    
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "❌ Error: Script no encontrado en $ScriptPath" -ForegroundColor Red
        return
    }
    
    try {
        Write-Host "Ejecutando: $PythonExe \"$ScriptPath\" --dry-run --verbose" -ForegroundColor Cyan
        
        $result = & $PythonExe "$ScriptPath" --dry-run --verbose 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Script ejecutado exitosamente" -ForegroundColor Green
            Write-Host "Salida:" -ForegroundColor Cyan
            $result | ForEach-Object { Write-Host "  $_" -ForegroundColor White }
        }
        else {
            Write-Host "❌ Error ejecutando script (código: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host "Salida:" -ForegroundColor Red
            $result | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        }
    }
    catch {
        Write-Host "❌ Error ejecutando script: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-Help {
    Write-Host "\n📖 Uso del script de configuración de tareas programadas" -ForegroundColor Yellow
    Write-Host "=" * 60 -ForegroundColor Yellow
    
    Write-Host "\nComandos disponibles:" -ForegroundColor Cyan
    Write-Host "  install   - Instalar tarea programada" -ForegroundColor White
    Write-Host "  uninstall - Eliminar tarea programada" -ForegroundColor White
    Write-Host "  status    - Mostrar estado de la tarea" -ForegroundColor White
    Write-Host "  test      - Probar script de expiración" -ForegroundColor White
    Write-Host "  help      - Mostrar esta ayuda" -ForegroundColor White
    
    Write-Host "\nParámetros opcionales:" -ForegroundColor Cyan
    Write-Host "  -IntervalMinutes <número>  - Intervalo en minutos (default: 10)" -ForegroundColor White
    Write-Host "  -ProjectPath <ruta>        - Ruta del proyecto (default: D:\INDICADORES SW\back)" -ForegroundColor White
    
    Write-Host "\nEjemplos:" -ForegroundColor Cyan
    Write-Host "  .\setup_scheduled_tasks.ps1 -Action install" -ForegroundColor White
    Write-Host "  .\setup_scheduled_tasks.ps1 -Action install -IntervalMinutes 5" -ForegroundColor White
    Write-Host "  .\setup_scheduled_tasks.ps1 -Action status" -ForegroundColor White
    Write-Host "  .\setup_scheduled_tasks.ps1 -Action test" -ForegroundColor White
    Write-Host "  .\setup_scheduled_tasks.ps1 -Action uninstall" -ForegroundColor White
}

# Verificar permisos de administrador para ciertas operaciones
function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Función principal
Write-Host "\n🤖 Configurador de Tareas Programadas - Trading Strategies" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green

switch ($Action.ToLower()) {
    "install" {
        if (-not (Test-AdminRights)) {
            Write-Host "⚠️ Advertencia: Se recomienda ejecutar como administrador para instalar tareas programadas" -ForegroundColor Yellow
            Write-Host "Continuando con permisos de usuario actual..." -ForegroundColor Yellow
        }
        Install-ScheduledTask
    }
    
    "uninstall" {
        Uninstall-ScheduledTask
    }
    
    "status" {
        Show-TaskStatus
    }
    
    "test" {
        Test-ExpireScript
    }
    
    "help" {
        Show-Help
    }
    
    default {
        Write-Host "❌ Acción no válida: $Action" -ForegroundColor Red
        Show-Help
        exit 1
    }
}

Write-Host "\n✅ Operación completada" -ForegroundColor Green