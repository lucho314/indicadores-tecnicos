#!/usr/bin/env python3
"""
Script para probar la conexión y operaciones de PostgreSQL en producción
"""
import os
import sys
from datetime import datetime

# Agregar el directorio actual al path para importar módulos
sys.path.append('/app')

from database.postgres_db_manager import PostgresIndicadorDB
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_postgres_connection():
    """Test de conexión a PostgreSQL"""
    print("🔗 === TEST DE CONEXIÓN A POSTGRESQL ===")
    
    # Mostrar variables de entorno
    print("\n📋 Variables de entorno:")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NO CONFIGURADA')}")
    print(f"DB_HOST: {os.getenv('DB_HOST', 'NO CONFIGURADA')}")
    print(f"DB_USER: {os.getenv('DB_USER', 'NO CONFIGURADA')}")
    print(f"DB_NAME: {os.getenv('DB_NAME', 'NO CONFIGURADA')}")
    
    try:
        # Intentar conexión
        print("\n🔌 Inicializando conexión a PostgreSQL...")
        db = PostgresIndicadorDB()
        print("✅ Conexión exitosa!")
        
        # Test de inserción
        print("\n💾 Probando inserción de datos...")
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": "BTC/USD",
            "interval": "4h",
            "close_price": 60000.50,
            "rsi": 45.2,
            "sma": 59500.75,
            "adx": 25.0,
            "macd": 120.5,
            "macd_signal": 115.0,
            "macd_hist": 5.5,
            "bb_upper": 61000,
            "bb_middle": 60000,
            "bb_lower": 59000
        }
        
        success = db.save_indicators(test_data, signal=False)
        print(f"Inserción: {'✅ Éxito' if success else '❌ Error'}")
        
        # Test de lectura
        print("\n📖 Probando lectura de datos...")
        recent = db.get_recent_indicators("BTC/USD", 5)
        print(f"Registros encontrados: {len(recent)}")
        
        if recent:
            print("📄 Último registro:")
            last_record = recent[0]
            print(f"  - Timestamp: {last_record.get('timestamp')}")
            print(f"  - Symbol: {last_record.get('symbol')}")
            print(f"  - Price: {last_record.get('price')}")
            print(f"  - RSI: {last_record.get('rsi')}")
            print(f"  - Signal: {last_record.get('signal')}")
        
        # Test de estadísticas
        print("\n📊 Probando estadísticas...")
        try:
            stats = db.get_execution_stats()
            print(f"Estadísticas obtenidas: {stats}")
        except Exception as e:
            print(f"⚠️ Error en estadísticas (no crítico): {e}")
        
        print("\n🎉 ¡Todos los tests completados exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en test de PostgreSQL: {e}")
        import traceback
        print(f"Traceback completo:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    exit(0 if success else 1)
