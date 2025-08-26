#!/usr/bin/env python3
"""
Script de debug para verificar los datos obtenidos de Bybit
"""

import sys
import os
from datetime import datetime
from service.klines_service import KlinesService
from service.technical_indicators import TechnicalIndicatorsCalculator
from database.postgres_db_manager import PostgresIndicadorDB

def debug_bybit_data():
    """
    Debug completo de los datos de Bybit
    """
    print("🔍 INICIANDO DEBUG DE DATOS DE BYBIT")
    print("=" * 50)
    
    # Inicializar servicios
    db = PostgresIndicadorDB()
    klines_service = KlinesService(db)
    calculator = TechnicalIndicatorsCalculator()
    
    symbol = "BTCUSDT"
    interval = "240"
    
    try:
        # 1. Obtener datos crudos de Bybit
        print(f"\n📥 1. OBTENIENDO DATOS CRUDOS DE BYBIT")
        print(f"Símbolo: {symbol}, Intervalo: {interval}")
        
        fresh_klines = klines_service.fetch_klines_from_api(
            symbol=symbol,
            interval=interval,
            limit=1000  # 1000 velas para análisis completo
        )
        
        print(f"✅ Obtenidas {len(fresh_klines)} velas para análisis completo")
        
        # Mostrar las primeras 3 velas crudas
        print("\n📋 PRIMERAS 3 VELAS CRUDAS:")
        for i, kline in enumerate(fresh_klines[:3]):
            print(f"Vela {i+1}:")
            print(f"  open_time: {kline['open_time']} ({datetime.fromtimestamp(kline['open_time']/1000)})")
            print(f"  close_time: {kline['close_time']} ({datetime.fromtimestamp(kline['close_time']/1000)})")
            print(f"  open_price: {kline['open_price']}")
            print(f"  high_price: {kline['high_price']}")
            print(f"  low_price: {kline['low_price']}")
            print(f"  close_price: {kline['close_price']}")
            print(f"  volume: {kline['volume']}")
            print()
        
        # 2. Calcular indicadores
        print(f"\n📊 2. CALCULANDO INDICADORES TÉCNICOS")
        
        indicators = calculator.calculate_all_indicators(fresh_klines)
        
        print(f"✅ Indicadores calculados")
        
        # Mostrar indicadores principales
        print("\n📈 INDICADORES PRINCIPALES:")
        print(f"  timestamp: {indicators.get('timestamp')} (tipo: {type(indicators.get('timestamp'))})")
        print(f"  symbol: {indicators.get('symbol')}")
        print(f"  interval: {indicators.get('interval')}")
        print(f"  close_price: {indicators.get('close_price')}")
        print(f"  rsi14: {indicators.get('rsi14')}")
        print(f"  ema20: {indicators.get('ema20')}")
        print(f"  ema200: {indicators.get('ema200')}")
        print(f"  sma20: {indicators.get('sma20')}")
        print(f"  macd: {indicators.get('macd')}")
        print(f"  macd_signal: {indicators.get('macd_signal')}")
        print(f"  macd_histogram: {indicators.get('macd_histogram')}")
        
        # 3. Verificar timestamp formatting
        print(f"\n🕐 3. VERIFICANDO TIMESTAMP")
        raw_timestamp = indicators.get('timestamp')
        print(f"  Raw timestamp: {raw_timestamp}")
        print(f"  Tipo: {type(raw_timestamp)}")
        
        if hasattr(raw_timestamp, 'isoformat'):
            formatted_timestamp = raw_timestamp.isoformat()
            print(f"  ISO format: {formatted_timestamp}")
        else:
            print(f"  No es un objeto datetime")
        
        # 4. Comparar con datos esperados
        print(f"\n🎯 4. COMPARACIÓN CON DATOS ESPERADOS")
        print(f"  Precio actual debería estar cerca de $111,000 para BTCUSDT")
        print(f"  Precio obtenido: ${indicators.get('close_price', 0):,.2f}")
        
        current_price = indicators.get('close_price', 0)
        if current_price > 200000:  # Si el precio es muy alto
            print(f"  ⚠️ PRECIO ANORMALMENTE ALTO - Posible error en datos")
        elif current_price < 50000:  # Si el precio es muy bajo
            print(f"  ⚠️ PRECIO ANORMALMENTE BAJO - Posible error en datos")
        else:
            print(f"  ✅ Precio dentro del rango esperado")
        
        # 5. Verificar última vela vs velas anteriores
        print(f"\n📊 5. COMPARACIÓN DE VELAS")
        if len(fresh_klines) >= 3:
            last_3_klines = fresh_klines[-3:]
            print("Últimas 3 velas:")
            for i, kline in enumerate(last_3_klines):
                dt = datetime.fromtimestamp(kline['open_time']/1000)
                print(f"  Vela {i+1}: {dt.strftime('%Y-%m-%d %H:%M')} - Close: ${kline['close_price']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR EN DEBUG: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_bybit_data()