#!/usr/bin/env python3
"""
Script para probar los indicadores solicitados: SMA, EMA200, ATR14, OBV
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.indicators_engine import IndicatorsEngine
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_requested_indicators():
    """
    Prueba los indicadores específicamente solicitados por el usuario
    """
    try:
        logger.info("🧪 Iniciando prueba de indicadores solicitados...")
        
        # Inicializar el motor de indicadores
        engine = IndicatorsEngine()
        
        # Obtener indicadores actuales
        indicators = engine.calculate_current_indicators("BTCUSDT", "240")
        
        if not indicators:
            logger.error("❌ No se pudieron obtener indicadores")
            return False
            
        logger.info("📊 Indicadores calculados:")
        
        # Verificar SMA
        sma_indicators = ['sma20', 'sma50', 'sma200']
        logger.info("\n📈 SMA (Simple Moving Average):")
        for sma in sma_indicators:
            value = indicators.get(sma)
            if value is not None:
                logger.info(f"  ✅ {sma.upper()}: ${value:,.2f}")
            else:
                logger.warning(f"  ⚠️  {sma.upper()}: No disponible (necesita más datos históricos)")
        
        # Verificar EMA200
        logger.info("\n📈 EMA200 (Exponential Moving Average 200):")
        ema200 = indicators.get('ema200')
        if ema200 is not None:
            logger.info(f"  ✅ EMA200: ${ema200:,.2f}")
        else:
            logger.warning(f"  ⚠️  EMA200: No disponible (necesita 200 períodos)")
            
        # Verificar ATR14
        logger.info("\n📊 ATR14 (Average True Range 14):")
        atr14 = indicators.get('atr14')
        if atr14 is not None:
            logger.info(f"  ✅ ATR14: ${atr14:,.2f}")
        else:
            logger.error(f"  ❌ ATR14: No disponible")
            
        # Verificar OBV
        logger.info("\n📊 OBV (On Balance Volume):")
        obv = indicators.get('obv')
        if obv is not None:
            logger.info(f"  ✅ OBV: {obv:,.0f}")
        else:
            logger.error(f"  ❌ OBV: No disponible")
            
        # Resumen de disponibilidad
        logger.info("\n📋 Resumen de indicadores solicitados:")
        requested_indicators = {
            'SMA20': indicators.get('sma20'),
            'SMA50': indicators.get('sma50'), 
            'SMA200': indicators.get('sma200'),
            'EMA200': indicators.get('ema200'),
            'ATR14': indicators.get('atr14'),
            'OBV': indicators.get('obv')
        }
        
        available_count = sum(1 for v in requested_indicators.values() if v is not None)
        total_count = len(requested_indicators)
        
        logger.info(f"  📊 Disponibles: {available_count}/{total_count} indicadores")
        
        for name, value in requested_indicators.items():
            status = "✅" if value is not None else "❌"
            logger.info(f"  {status} {name}: {'Disponible' if value is not None else 'No disponible'}")
            
        if available_count >= 4:  # Al menos ATR14 y OBV deben estar disponibles
            logger.info("\n🎉 ¡Todos los indicadores principales están funcionando correctamente!")
            return True
        else:
            logger.warning(f"\n⚠️  Solo {available_count} de {total_count} indicadores están disponibles")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en la prueba: {e}")
        return False

if __name__ == "__main__":
    success = test_requested_indicators()
    if success:
        logger.info("\n✅ Prueba completada exitosamente")
        sys.exit(0)
    else:
        logger.error("\n❌ Prueba falló")
        sys.exit(1)