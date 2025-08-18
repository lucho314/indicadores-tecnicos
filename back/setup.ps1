# Script PowerShell para construir y ejecutar la aplicación Dockerizada

Write-Host "🚀 Crypto Indicators - Docker Setup" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Verificar que existe el archivo .env
if (!(Test-Path ".env")) {
    Write-Host "⚠️  Archivo .env no encontrado. Copiando desde .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "📝 Por favor edita el archivo .env con tus API keys reales antes de continuar." -ForegroundColor Yellow
    Write-Host "   Presiona Enter cuando hayas configurado las variables..." -ForegroundColor Yellow
    Read-Host
}

# Crear directorio de logs si no existe
if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force
}

Write-Host "🏗️  Construyendo contenedores Docker..." -ForegroundColor Blue
docker-compose build

Write-Host "🗄️  Iniciando base de datos PostgreSQL..." -ForegroundColor Blue
docker-compose up -d postgres

Write-Host "⏳ Esperando que PostgreSQL esté listo..." -ForegroundColor Yellow
Start-Sleep 10

Write-Host "✅ Ejecutando migración de base de datos..." -ForegroundColor Green
docker-compose run --rm app python -c @"
from database.postgres_db_manager import PostgresIndicadorDB
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Esperar conexión a BD
for i in range(30):
    try:
        db = PostgresIndicadorDB()
        logger.info('✅ Conexión a PostgreSQL establecida')
        break
    except Exception as e:
        logger.info(f'⏳ Esperando PostgreSQL... intento {i+1}/30')
        time.sleep(2)
else:
    logger.error('❌ No se pudo conectar a PostgreSQL')
    exit(1)
"@

Write-Host "🎯 Iniciando aplicación completa..." -ForegroundColor Green
docker-compose up -d

Write-Host ""
Write-Host "✅ ¡Aplicación iniciada exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Para ver los logs:" -ForegroundColor Cyan
Write-Host "   docker-compose logs -f app" -ForegroundColor White
Write-Host "   docker-compose logs -f scheduler" -ForegroundColor White
Write-Host ""
Write-Host "🗄️  Para acceder a PostgreSQL:" -ForegroundColor Cyan
Write-Host "   docker-compose exec postgres psql -U indicadores_user -d indicadores_db" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Para detener la aplicación:" -ForegroundColor Cyan
Write-Host "   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Para reiniciar:" -ForegroundColor Cyan
Write-Host "   docker-compose restart" -ForegroundColor White
