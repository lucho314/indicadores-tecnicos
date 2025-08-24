#!/usr/bin/env python3
"""
Script de instalación y configuración del nuevo sistema de indicadores
Ejecuta la migración de base de datos y configura el sistema
"""

import os
import sys
import logging
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.postgres_db_manager import PostgresIndicadorDB
from service.indicators_engine import IndicatorsEngine

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """
    Verifica que todas las dependencias estén instaladas
    """
    try:
        logger.info("🔍 Verificando dependencias...")
        
        # Verificar pandas_ta
        try:
            import pandas_ta as ta
            logger.info(f"✅ pandas_ta versión: {ta.__version__}")
        except ImportError:
            logger.error("❌ pandas_ta no está instalado")
            logger.info("💡 Ejecuta: pip install pandas-ta==0.3.14b0")
            return False
            
        # Verificar pandas
        try:
            import pandas as pd
            logger.info(f"✅ pandas versión: {pd.__version__}")
        except ImportError:
            logger.error("❌ pandas no está instalado")
            logger.info("💡 Ejecuta: pip install pandas==2.1.4")
            return False
            
        # Verificar pybit
        try:
            import pybit
            logger.info("✅ pybit disponible")
        except ImportError:
            logger.error("❌ pybit no está instalado")
            return False
            
        # Verificar psycopg2
        try:
            import psycopg2
            logger.info("✅ psycopg2 disponible")
        except ImportError:
            logger.error("❌ psycopg2 no está instalado")
            return False
            
        logger.info("✅ Todas las dependencias están disponibles")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando dependencias: {e}")
        return False

def setup_database():
    """
    Configura la base de datos ejecutando las migraciones
    """
    try:
        logger.info("🗄️ Configurando base de datos...")
        
        # Verificar conexión
        db_manager = PostgresIndicadorDB()
        logger.info("✅ Conexión a PostgreSQL exitosa")
        
        # Ejecutar migración
        script_path = os.path.join(os.path.dirname(__file__), "database", "create_klines_table.sql")
        
        if not os.path.exists(script_path):
            logger.error(f"❌ Script de migración no encontrado: {script_path}")
            return False
            
        logger.info("📄 Ejecutando migración de base de datos...")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # Ejecutar script completo
                cur.execute(sql_script)
                conn.commit()
                
        logger.info("✅ Migración de base de datos completada")
        
        # Verificar que las tablas se crearon
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('klines', 'indicadores')
                """)
                tables = [row[0] for row in cur.fetchall()]
                
        logger.info(f"📊 Tablas disponibles: {', '.join(tables)}")
        
        if 'klines' in tables:
            logger.info("✅ Tabla 'klines' creada exitosamente")
        else:
            logger.error("❌ Tabla 'klines' no se creó")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando base de datos: {e}")
        return False

def initialize_system():
    """
    Inicializa el sistema con datos iniciales
    """
    try:
        logger.info("🚀 Inicializando sistema de indicadores...")
        
        engine = IndicatorsEngine()
        
        # Inicializar para BTCUSDT 4h
        success = engine.initialize_system(symbol="BTCUSDT", interval="240")
        
        if success:
            logger.info("✅ Sistema inicializado exitosamente")
            
            # Obtener estado del sistema
            status = engine.get_system_status("BTCUSDT", "240")
            logger.info(f"📊 Velas sincronizadas: {status.get('klines_count', 0)}")
            logger.info(f"⏰ Última vela: {status.get('latest_kline_time', 'N/A')}")
            
            # Obtener últimos indicadores
            indicators = engine.get_latest_indicators("BTCUSDT")
            if indicators:
                logger.info("📈 Indicadores calculados:")
                logger.info(f"   💰 Precio: ${indicators.get('price', 0):.2f}")
                logger.info(f"   📊 RSI: {indicators.get('rsi', 0):.2f}")
                logger.info(f"   📈 MACD Hist: {indicators.get('macd_hist', 0):.4f}")
                
            return True
        else:
            logger.error("❌ Error inicializando sistema")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error inicializando sistema: {e}")
        return False

def test_integration():
    """
    Prueba la integración con el sistema existente
    """
    try:
        logger.info("🧪 Probando integración con sistema existente...")
        
        # Importar la función principal
        from service.indicadores_tecnicos import obtener_indicadores
        
        # Probar la función
        result = obtener_indicadores("BTCUSDT", "240")
        
        if result and not result.get("errors"):
            logger.info("✅ Integración exitosa")
            logger.info(f"📊 Fuente de datos: {result.get('source', 'unknown')}")
            logger.info(f"💰 Precio obtenido: ${result.get('close_price', 0):.2f}")
            logger.info(f"📈 RSI: {result.get('rsi14', 0):.2f}")
            return True
        else:
            logger.error(f"❌ Error en integración: {result.get('errors', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando integración: {e}")
        return False

def create_backup_script():
    """
    Crea un script de respaldo para el sistema anterior
    """
    try:
        logger.info("💾 Creando script de respaldo...")
        
        backup_content = '''
# Script de respaldo - Sistema anterior de indicadores
# Para usar el sistema anterior, cambia la importación en tu código:

# En lugar de:
# from service.indicadores_tecnicos import obtener_indicadores

# Usa:
# from service.indicadores_tecnicos import obtener_indicadores_legacy as obtener_indicadores

# O ejecuta directamente:
# python -c "from service.indicadores_tecnicos import obtener_indicadores_legacy; print(obtener_indicadores_legacy())"
'''
        
        backup_path = os.path.join(os.path.dirname(__file__), "BACKUP_INSTRUCTIONS.txt")
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
            
        logger.info(f"✅ Instrucciones de respaldo creadas: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando respaldo: {e}")
        return False

def main():
    """
    Función principal de instalación
    """
    logger.info("🚀 INSTALACIÓN DEL NUEVO SISTEMA DE INDICADORES")
    logger.info("=" * 60)
    logger.info("Este script configurará el nuevo sistema que:")
    logger.info("• Obtiene datos directamente de Bybit")
    logger.info("• Calcula indicadores con pandas_ta")
    logger.info("• Mantiene compatibilidad con el sistema anterior")
    logger.info("=" * 60)
    
    steps = [
        ("Verificar dependencias", check_dependencies),
        ("Configurar base de datos", setup_database),
        ("Inicializar sistema", initialize_system),
        ("Probar integración", test_integration),
        ("Crear respaldo", create_backup_script)
    ]
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        logger.info(f"\n📋 Paso {i}/{len(steps)}: {step_name}")
        logger.info("-" * 40)
        
        try:
            success = step_func()
            
            if success:
                logger.info(f"✅ {step_name}: COMPLETADO")
            else:
                logger.error(f"❌ {step_name}: FALLIDO")
                logger.error("🛑 Instalación interrumpida")
                return False
                
        except Exception as e:
            logger.error(f"💥 {step_name}: ERROR - {e}")
            logger.error("🛑 Instalación interrumpida")
            return False
    
    # Instalación completada
    logger.info("\n" + "=" * 60)
    logger.info("🎉 ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!")
    logger.info("=" * 60)
    logger.info("\n📋 PRÓXIMOS PASOS:")
    logger.info("1. El sistema está listo para usar")
    logger.info("2. La función obtener_indicadores() ahora usa el nuevo sistema")
    logger.info("3. Los datos se sincronizan automáticamente desde Bybit")
    logger.info("4. Se mantiene compatibilidad con el código existente")
    logger.info("\n🧪 PARA PROBAR:")
    logger.info("   python test_new_indicators.py")
    logger.info("\n📊 PARA USAR EN TU CÓDIGO:")
    logger.info("   from service.indicadores_tecnicos import obtener_indicadores")
    logger.info("   data = obtener_indicadores('BTCUSDT', '240')")
    logger.info("\n💾 RESPALDO:")
    logger.info("   Ver BACKUP_INSTRUCTIONS.txt para usar el sistema anterior")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Instalación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error fatal en instalación: {e}")
        sys.exit(1)