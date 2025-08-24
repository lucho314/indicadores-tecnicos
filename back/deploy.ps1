#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script de configuración post-despliegue para Windows
    
.DESCRIPTION
    Ejecuta la configuración automática después del despliegue
    Verifica que la base de datos esté lista y sincroniza datos
    
.PARAMETER Action
    Acción a ejecutar: setup, test, status, sync
    
.EXAMPLE
    .\deploy.ps1 setup
    .\deploy.ps1 test
    .\deploy.ps1 status
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("setup", "test", "status", "sync", "help")]
    [string]$Action = "setup"
)

# Colores para output
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Cyan = "Cyan"

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-Header {
    Write-ColorOutput "" 
    Write-ColorOutput "🚀 SISTEMA DE INDICADORES TÉCNICOS - DESPLIEGUE" $Cyan
    Write-ColorOutput "============================================================" $Cyan
    Write-ColorOutput "📅 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" $Yellow
    Write-ColorOutput ""
}

function Show-Help {
    Write-ColorOutput "📋 COMANDOS DISPONIBLES:" $Cyan
    Write-ColorOutput ""
    Write-ColorOutput "  setup   - Configuración completa post-despliegue (recomendado)" $Green
    Write-ColorOutput "  test    - Probar análisis completo del sistema" $Green  
    Write-ColorOutput "  status  - Ver estado actual del sistema" $Green
    Write-ColorOutput "  sync    - Sincronizar datos manualmente" $Green
    Write-ColorOutput "  help    - Mostrar esta ayuda" $Green
    Write-ColorOutput ""
    Write-ColorOutput "💡 EJEMPLOS:" $Yellow
    Write-ColorOutput "  .\deploy.ps1 setup    # Configuración inicial"
    Write-ColorOutput "  .\deploy.ps1 test     # Probar sistema"
    Write-ColorOutput "  .\deploy.ps1 status   # Ver estado"
    Write-ColorOutput ""
}

function Test-DockerCompose {
    try {
        $result = docker-compose --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "✅ Docker Compose disponible" $Green
            return $true
        }
    } catch {
        Write-ColorOutput "❌ Docker Compose no encontrado" $Red
        Write-ColorOutput "💡 Instala Docker Desktop: https://www.docker.com/products/docker-desktop" $Yellow
        return $false
    }
    return $false
}

function Invoke-Setup {
    Write-ColorOutput "🔧 EJECUTANDO CONFIGURACIÓN POST-DESPLIEGUE..." $Cyan
    Write-ColorOutput ""
    
    try {
        Write-ColorOutput "📦 Ejecutando script de configuración..." $Yellow
        $result = docker-compose run --rm app python deploy_setup.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "" 
            Write-ColorOutput "🎉 CONFIGURACIÓN COMPLETADA EXITOSAMENTE" $Green
            Write-ColorOutput "" 
            Write-ColorOutput "📋 Próximos pasos:" $Cyan
            Write-ColorOutput "  1. Sistema listo para análisis automático" $Green
            Write-ColorOutput "  2. Ejecuta: .\deploy.ps1 test (para probar)" $Green
            Write-ColorOutput "  3. Ejecuta: .\deploy.ps1 status (para ver estado)" $Green
        } else {
            Write-ColorOutput "❌ Error en configuración" $Red
            Write-ColorOutput "💡 Revisa los logs arriba para más detalles" $Yellow
        }
    } catch {
        Write-ColorOutput "❌ Error ejecutando configuración: $($_.Exception.Message)" $Red
    }
}

function Invoke-Test {
    Write-ColorOutput "🧪 PROBANDO ANÁLISIS COMPLETO..." $Cyan
    Write-ColorOutput ""
    
    try {
        Write-ColorOutput "📊 Ejecutando análisis de indicadores..." $Yellow
        $result = docker-compose run --rm app python main.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "" 
            Write-ColorOutput "✅ ANÁLISIS COMPLETADO EXITOSAMENTE" $Green
            Write-ColorOutput "🎯 El sistema está funcionando correctamente" $Green
        } else {
            Write-ColorOutput "❌ Error en análisis" $Red
            Write-ColorOutput "💡 Ejecuta: .\deploy.ps1 setup (para reconfigurar)" $Yellow
        }
    } catch {
        Write-ColorOutput "❌ Error ejecutando análisis: $($_.Exception.Message)" $Red
    }
}

function Invoke-Status {
    Write-ColorOutput "📊 VERIFICANDO ESTADO DEL SISTEMA..." $Cyan
    Write-ColorOutput ""
    
    try {
        Write-ColorOutput "🔍 Obteniendo estado del motor de indicadores..." $Yellow
        $result = docker-compose run --rm app python -c "from service.indicators_engine import IndicatorsEngine; import json; print(json.dumps(IndicatorsEngine().get_system_status(), indent=2, default=str))"
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "" 
            Write-ColorOutput "✅ ESTADO OBTENIDO EXITOSAMENTE" $Green
        } else {
            Write-ColorOutput "❌ Error obteniendo estado" $Red
        }
    } catch {
        Write-ColorOutput "❌ Error verificando estado: $($_.Exception.Message)" $Red
    }
}

function Invoke-Sync {
    Write-ColorOutput "🔄 SINCRONIZANDO DATOS..." $Cyan
    Write-ColorOutput ""
    
    try {
        Write-ColorOutput "📥 Ejecutando sincronización incremental..." $Yellow
        $result = docker-compose run --rm app python -c "from service.klines_service import KlinesService; print(f'Velas sincronizadas: {KlinesService().incremental_sync()}')"
        
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "" 
            Write-ColorOutput "✅ SINCRONIZACIÓN COMPLETADA" $Green
        } else {
            Write-ColorOutput "❌ Error en sincronización" $Red
        }
    } catch {
        Write-ColorOutput "❌ Error sincronizando: $($_.Exception.Message)" $Red
    }
}

# Script principal
Show-Header

if (-not (Test-DockerCompose)) {
    exit 1
}

switch ($Action.ToLower()) {
    "setup" {
        Invoke-Setup
    }
    "test" {
        Invoke-Test  
    }
    "status" {
        Invoke-Status
    }
    "sync" {
        Invoke-Sync
    }
    "help" {
        Show-Help
    }
    default {
        Write-ColorOutput "❌ Acción no válida: $Action" $Red
        Show-Help
        exit 1
    }
}

Write-ColorOutput ""
Write-ColorOutput "🔧 Para más comandos: .\deploy.ps1 help" $Cyan
Write-ColorOutput "📖 Documentación completa: DEPLOY_INSTRUCTIONS.md" $Cyan
Write-ColorOutput ""