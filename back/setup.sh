#!/bin/bash

# Script para construir y ejecutar la aplicación Dockerizada

echo "🚀 Crypto Indicators - Docker Setup"
echo "=================================="

# Verificar que existe el archivo .env
if [ ! -f .env ]; then
    echo "⚠️  Archivo .env no encontrado. Copiando desde .env.example..."
    cp .env.example .env
    echo "📝 Por favor edita el archivo .env con tus API keys reales antes de continuar."
    echo "   Presiona Enter cuando hayas configurado las variables..."
    read
fi

# Crear directorio de logs si no existe
mkdir -p logs

echo "🏗️  Construyendo contenedores Docker..."
docker-compose build

echo "🗄️  Iniciando base de datos PostgreSQL..."
docker-compose up -d postgres

echo "⏳ Esperando que PostgreSQL esté listo..."
sleep 10

echo "✅ Ejecutando migración de base de datos..."
docker-compose run --rm app python -c "
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
"

echo "🎯 Iniciando aplicación completa..."
docker-compose up -d

echo ""
echo "✅ ¡Aplicación iniciada exitosamente!"
echo ""
echo "📊 Para ver los logs:"
echo "   docker-compose logs -f app"
echo "   docker-compose logs -f scheduler"
echo ""
echo "🗄️  Para acceder a PostgreSQL:"
echo "   docker-compose exec postgres psql -U indicadores_user -d indicadores_db"
echo ""
echo "🛑 Para detener la aplicación:"
echo "   docker-compose down"
echo ""
echo "🔄 Para reiniciar:"
echo "   docker-compose restart"
