#!/usr/bin/env python3
"""
Script para comparar diferentes fuentes de datos de Bybit
y identificar discrepancias en precios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.bybit_service import BybitService
from service.klines_service import KlinesService
from database.postgres_db_manager import PostgresIndicadorDB
from datetime import datetime

def compare_bybit_sources():
    """
    Compara datos de diferentes fuentes de Bybit:
    1. Precio actual del ticker
    2. Última vela de klines
    3. Datos históricos
    """
    print("🔍 COMPARANDO FUENTES DE DATOS DE BYBIT")
    print("=" * 50)
    
    symbol = "BTCUSDT"
    interval = "240"  # 4 horas
    
    try:
        # Inicializar servicios
        db = PostgresIndicadorDB()
        bybit_service = BybitService()
        klines_service = KlinesService(db)
        
        print(f"📊 Analizando símbolo: {symbol}")
        print(f"⏰ Intervalo: {interval} (4 horas)")
        print()
        
        # 1. Obtener precio actual del ticker
        print("1️⃣ PRECIO ACTUAL DEL TICKER")
        print("-" * 30)
        try:
            current_price = bybit_service.get_price(symbol)
            print(f"💰 Precio del ticker: ${current_price:,.2f}")
        except Exception as e:
            print(f"❌ Error obteniendo precio del ticker: {e}")
            current_price = None
        
        print()
        
        # 2. Obtener última vela de klines
        print("2️⃣ ÚLTIMA VELA DE KLINES")
        print("-" * 30)
        try:
            # Obtener solo las últimas 3 velas para comparar
            recent_klines = klines_service.get_klines_from_api(symbol, interval, limit=3)
            
            if recent_klines and len(recent_klines) > 0:
                latest_kline = recent_klines[0]  # La más reciente
                
                print(f"📅 Timestamp: {datetime.fromtimestamp(latest_kline['open_time']/1000)}")
                print(f"🔓 Precio apertura: ${latest_kline['open_price']:,.2f}")
                print(f"📈 Precio máximo: ${latest_kline['high_price']:,.2f}")
                print(f"📉 Precio mínimo: ${latest_kline['low_price']:,.2f}")
                print(f"🔒 Precio cierre: ${latest_kline['close_price']:,.2f}")
                print(f"📊 Volumen: {latest_kline['volume']:,.3f}")
                
                kline_close_price = latest_kline['close_price']
            else:
                print("❌ No se pudieron obtener klines")
                kline_close_price = None
                
        except Exception as e:
            print(f"❌ Error obteniendo klines: {e}")
            kline_close_price = None
        
        print()
        
        # 3. Comparar precios
        print("3️⃣ COMPARACIÓN DE PRECIOS")
        print("-" * 30)
        
        if current_price and kline_close_price:
            difference = abs(current_price - kline_close_price)
            percentage_diff = (difference / kline_close_price) * 100
            
            print(f"💰 Precio ticker: ${current_price:,.2f}")
            print(f"🕯️ Precio kline: ${kline_close_price:,.2f}")
            print(f"📊 Diferencia: ${difference:,.2f}")
            print(f"📈 Diferencia %: {percentage_diff:.4f}%")
            
            if percentage_diff > 1.0:  # Más del 1% de diferencia
                print("⚠️ ALERTA: Diferencia significativa detectada!")
                print("🔍 Posibles causas:")
                print("   - Diferentes mercados (spot vs futures)")
                print("   - Datos de diferentes timeframes")
                print("   - Latencia en la sincronización")
                print("   - Configuración incorrecta de la API")
            else:
                print("✅ Precios consistentes")
        else:
            print("❌ No se pueden comparar precios (datos faltantes)")
        
        print()
        
        # 4. Verificar configuración de API
        print("4️⃣ VERIFICACIÓN DE CONFIGURACIÓN")
        print("-" * 30)
        
        try:
            # Verificar conexión
            test_result = bybit_service.test_connection()
            print(f"🔗 Conexión API: {'✅ OK' if test_result else '❌ Error'}")
            
            # Verificar si estamos en testnet o mainnet
            print(f"🌐 Entorno: {os.getenv('APP_ENV', 'No configurado')}")
            print(f"🔑 API Key configurada: {'✅ Sí' if os.getenv('BYBIT_API_KEY') else '❌ No'}")
            print(f"🔐 API Secret configurada: {'✅ Sí' if os.getenv('BYBIT_API_SECRET') else '❌ No'}")
            
        except Exception as e:
            print(f"❌ Error verificando configuración: {e}")
        
        print()
        print("🏁 ANÁLISIS COMPLETADO")
        print("=" * 50)
        
    except Exception as e:
        print(f"💥 ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_bybit_sources()