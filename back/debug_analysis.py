#!/usr/bin/env python3
"""
Script para debuggear el análisis de indicadores en producción
Ejecuta el análisis manual de BTC/USDT con debug detallado
"""
import os
import sys
import json
import subprocess
import logging
from datetime import datetime

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_manual_analysis():
    """Ejecutar análisis manual con debug completo"""
    print("🔍 === DEBUG ANÁLISIS MANUAL BTC/USDT ===")
    
    # Mostrar variables de entorno importantes
    print("\n📋 Variables de entorno clave:")
    env_vars = [
        'TWELVEDATA_API_KEY', 'OPENAI_API_KEY', 'DATABASE_URL',
        'DB_HOST', 'DB_USER', 'DB_NAME', 'WHATSAPP_PHONE'
    ]
    
    for var in env_vars:
        value = os.getenv(var, 'NO CONFIGURADA')
        # Ocultar datos sensibles
        if 'KEY' in var and value != 'NO CONFIGURADA':
            display_value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else value
        else:
            display_value = value
        print(f"  {var}: {display_value}")
    
    # Verificar que el archivo main.py existe
    main_path = '/app/main.py'
    if not os.path.exists(main_path):
        print(f"❌ No se encuentra {main_path}")
        return False
    
    print(f"✅ {main_path} encontrado")
    
    # Test 1: Ejecutar con BTC/USD (como está configurado)
    print("\n🚀 TEST 1: Ejecutando análisis BTC/USD...")
    try:
        result = subprocess.run(
            ['python', main_path, '--symbol', 'BTC/USD', '--json'],
            capture_output=True,
            text=True,
            timeout=300,
            cwd='/app'
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT ({len(result.stdout)} chars):")
        print(result.stdout)
        print(f"STDERR ({len(result.stderr)} chars):")
        print(result.stderr)
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout después de 5 minutos")
    except Exception as e:
        print(f"❌ Error ejecutando: {e}")
    
    # Test 2: Ejecutar con BTCUSDT (formato Bybit)
    print("\n🚀 TEST 2: Ejecutando análisis BTCUSDT...")
    try:
        result = subprocess.run(
            ['python', main_path, '--symbol', 'BTCUSDT', '--json'],
            capture_output=True,
            text=True,
            timeout=300,
            cwd='/app'
        )
        
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT ({len(result.stdout)} chars):")
        print(result.stdout)
        print(f"STDERR ({len(result.stderr)} chars):")
        print(result.stderr)
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout después de 5 minutos")
    except Exception as e:
        print(f"❌ Error ejecutando: {e}")
    
    # Test 3: Verificar la estructura del directorio
    print("\n📁 Estructura del directorio /app:")
    try:
        for root, dirs, files in os.walk('/app'):
            level = root.replace('/app', '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Solo primeros 10 archivos
                print(f"{subindent}{file}")
            if len(files) > 10:
                print(f"{subindent}... y {len(files) - 10} archivos más")
    except Exception as e:
        print(f"Error listando directorio: {e}")
    
    # Test 4: Probar importaciones directas
    print("\n🔗 TEST 4: Probando importaciones directas...")
    try:
        sys.path.append('/app')
        import service.indicadores_tecnicos as indicadores_svc
        print("✅ indicadores_tecnicos importado correctamente")
        
        from database.postgres_db_manager import PostgresIndicadorDB
        print("✅ PostgresIndicadorDB importado correctamente")
        
        # Probar crear instancia de BD
        db = PostgresIndicadorDB()
        print("✅ Conexión a BD exitosa")
        
        # Probar obtener datos de API directamente
        print("🌐 Probando obtener datos de TwelveData API...")
        try:
            result = indicadores_svc.obtener_indicadores('BTC/USD', '4h')
            print(f"✅ Datos obtenidos de API: {type(result)}")
            if isinstance(result, dict):
                print(f"   Keys: {list(result.keys())}")
                print(f"   Muestra: {str(result)[:200]}...")
                
                # Verificar si hay datos válidos
                if 'timestamp' in result:
                    print(f"   ✅ Timestamp encontrado: {result.get('timestamp')}")
                if 'rsi' in result:
                    print(f"   ✅ RSI encontrado: {result.get('rsi')}")
                if 'close_price' in result or 'price' in result:
                    price = result.get('close_price') or result.get('price')
                    print(f"   ✅ Precio encontrado: {price}")
        except Exception as api_error:
            print(f"❌ Error obteniendo datos de API: {api_error}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error en importaciones: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Debug completado")

if __name__ == "__main__":
    test_manual_analysis()
