#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script optimizado para ejecutar el servidor API con configuración mejorada de concurrencia.

.DESCRIPTION
    Este script resuelve el problema de encolamiento de peticiones WebSocket y APIs REST
    ejecutando uvicorn con configuración optimizada para concurrencia.

.PARAMETER Environment
    Entorno de ejecución: 'development' o 'production'

.PARAMETER Workers
    Número de workers a usar (opcional, se calcula automáticamente si no se especifica)

.EXAMPLE
    .\run_optimized.ps1 -Environment development
    .\run_optimized.ps1 -Environment production -Workers 4
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('development', 'production')]
    [string]$Environment = 'development',
    
    [Parameter(Mandatory=$false)]
    [int]$Workers = 0
)

# Configurar variables de entorno
$env:APP_ENV = $Environment

if ($Workers -gt 0) {
    $env:UVICORN_WORKERS = $Workers
}

# Colores para output
$Green = "`e[32m"
$Yellow = "`e[33m"
$Red = "`e[31m"
$Reset = "`e[0m"

Write-Host "${Green}🚀 Iniciando servidor API optimizado${Reset}"
Write-Host "${Yellow}📊 Entorno: $Environment${Reset}"

if ($Workers -gt 0) {
    Write-Host "${Yellow}👥 Workers: $Workers${Reset}"
} else {
    Write-Host "${Yellow}👥 Workers: Auto (basado en CPU cores)${Reset}"
}

Write-Host "${Yellow}🔧 Configuración optimizada para WebSocket + REST API${Reset}"
Write-Host ""

try {
    if ($Environment -eq 'development') {
        # Desarrollo: usar configuración con reload
        Write-Host "${Green}🔄 Modo desarrollo con auto-reload${Reset}"
        python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --reload --reload-dir ./api --reload-dir ./service
    } else {
        # Producción: usar configuración optimizada
        Write-Host "${Green}🏭 Modo producción optimizado${Reset}"
        python uvicorn_config.py
    }
} catch {
    Write-Host "${Red}❌ Error ejecutando servidor: $_${Reset}"
    exit 1
}