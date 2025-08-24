#!/usr/bin/env python3
"""
Script de prueba para el nuevo sistema de indicadores técnicos
Prueba la reingeniería completa: sincronización de Bybit + cálculo con pandas_ta
"""

import os
import sys
import logging
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.indicators_engine import IndicatorsEngine
from database.postgres_db_manager import PostgresIndicadorDB

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """
    Prueba la conexión a la base de datos
    """
    try:
        logger.info("🔍 Probando conexión a la base de datos...")
        db_manager = PostgresIndicadorDB()
        logger.info("✅ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error de conexión a BD: {e}")
        return False

def test_klines_api():
    """
    Prueba la obtención de datos desde la API de Bybit
    """
    try:
        logger.info("🔍 Probando API de Bybit...")
        from service.klines_service import KlinesService
        
        klines_service = KlinesService()
        klines = klines_service.fetch_klines_from_api(
            symbol="BTCUSDT", 
            interval="240", 
            limit=10
        )
        
        if klines and len(klines) > 0:
            logger.info(f"✅ API de Bybit funcionando - obtenidas {len(klines)} velas")
            logger.info(f"📊 Última vela: ${klines[-1]['close_price']:.2f}")
            return True
        else:
            logger.error("❌ No se obtuvieron datos de la API")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando API: {e}")
        return False

def test_indicators_calculation():
    """
    Prueba el cálculo de indicadores técnicos
    """
    try:
        logger.info("🔍 Probando cálculo de indicadores...")
        from service.klines_service import KlinesService
        from service.technical_indicators import TechnicalIndicatorsCalculator
        
        # Obtener datos de prueba
        klines_service = KlinesService()
        klines = klines_service.fetch_klines_from_api(
            symbol="BTCUSDT", 
            interval="240", 
            limit=200  # Suficiente para todos los indicadores
        )
        
        if not klines or len(klines) < 20:
            logger.error(f"❌ Insuficientes velas para prueba: {len(klines) if klines else 0}")
            return False
            
        # Calcular indicadores
        calculator = TechnicalIndicatorsCalculator()
        indicators = calculator.calculate_all_indicators(klines)
        
        if indicators:
            logger.info("✅ Indicadores calculados exitosamente")
            logger.info(f"📈 Precio: ${indicators.get('close_price', 0):.2f}")
            logger.info(f"📊 RSI14: {indicators.get('rsi14', 0):.2f}")
            logger.info(f"📈 EMA20: ${indicators.get('ema20', 0):.2f}")
            logger.info(f"📈 EMA200: ${indicators.get('ema200', 'N/A')}")
            logger.info(f"📊 MACD: {indicators.get('macd', 0):.4f}")
            logger.info(f"📊 ATR14: ${indicators.get('atr14', 0):.2f}")
            logger.info(f"📊 ADX14: {indicators.get('adx14', 0):.2f}")
            
            # Validar indicadores
            if calculator.validate_indicators(indicators):
                logger.info("✅ Indicadores validados correctamente")
                return True
            else:
                logger.error("❌ Indicadores no pasaron validación")
                return False
        else:
            logger.error("❌ No se pudieron calcular indicadores")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error calculando indicadores: {e}")
        return False

def test_full_system():
    """
    Prueba el sistema completo de principio a fin
    """
    try:
        logger.info("🔍 Probando sistema completo...")
        
        # Inicializar motor de indicadores
        engine = IndicatorsEngine()
        
        # Obtener estado inicial
        initial_status = engine.get_system_status()
        logger.info(f"📊 Estado inicial: {initial_status['klines_count']} velas")
        
        # Ejecutar ciclo completo
        result = engine.run_full_update_cycle(symbol="BTCUSDT", interval="240")
        
        if result.get("success"):
            logger.info(f"✅ Sistema completo funcionando - tiempo: {result['execution_time']:.2f}s")
            
            # Mostrar indicadores finales
            latest = result.get("latest_indicators")
            if latest:
                logger.info("📊 Indicadores finales:")
                logger.info(f"   💰 Precio: ${latest.get('price', 0):.2f}")
                logger.info(f"   📈 RSI: {latest.get('rsi', 0):.2f}")
                logger.info(f"   📊 MACD Hist: {latest.get('macd_hist', 0):.4f}")
                
            return True
        else:
            logger.error(f"❌ Error en sistema completo: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando sistema completo: {e}")
        return False

def run_performance_test():
    """
    Prueba de rendimiento del sistema
    """
    try:
        logger.info("🔍 Ejecutando prueba de rendimiento...")
        
        engine = IndicatorsEngine()
        
        # Medir tiempo de actualización
        start_time = datetime.now()
        
        for i in range(3):
            logger.info(f"🔄 Iteración {i+1}/3")
            result = engine.update_data(symbol="BTCUSDT", interval="240")
            
            if not result:
                logger.error(f"❌ Fallo en iteración {i+1}")
                return False
                
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        avg_time = total_time / 3
        
        logger.info(f"✅ Prueba de rendimiento completada")
        logger.info(f"⏱️ Tiempo total: {total_time:.2f}s")
        logger.info(f"⏱️ Tiempo promedio: {avg_time:.2f}s por actualización")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en prueba de rendimiento: {e}")
        return False

def main():
    """
    Función principal que ejecuta todas las pruebas
    """
    logger.info("🚀 Iniciando pruebas del nuevo sistema de indicadores")
    logger.info("=" * 60)
    
    tests = [
        ("Conexión a Base de Datos", test_database_connection),
        ("API de Bybit", test_klines_api),
        ("Cálculo de Indicadores", test_indicators_calculation),
        ("Sistema Completo", test_full_system),
        ("Rendimiento", run_performance_test)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Ejecutando: {test_name}")
        logger.info("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                logger.info(f"✅ {test_name}: EXITOSO")
            else:
                logger.error(f"❌ {test_name}: FALLIDO")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📋 RESUMEN DE PRUEBAS")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ EXITOSO" if success else "❌ FALLIDO"
        logger.info(f"{test_name:.<30} {status}")
        if success:
            passed += 1
    
    logger.info("-" * 60)
    logger.info(f"📊 Resultado: {passed}/{total} pruebas exitosas ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        return True
    else:
        logger.error(f"⚠️ {total-passed} pruebas fallaron. Revisar errores arriba.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Error fatal: {e}")
        sys.exit(1)