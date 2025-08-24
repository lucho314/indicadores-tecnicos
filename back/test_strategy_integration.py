#!/usr/bin/env python3
"""
Test de integración del sistema de estrategias de trading
Prueba la inserción y consulta de estrategias sin depender del LLM
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime, timedelta
from database.postgres_db_manager import PostgresIndicadorDB
from service.trading_strategy_service import TradingStrategyService
import requests
import json

def test_strategy_integration():
    print("🚀 TEST DE INTEGRACIÓN - SISTEMA DE ESTRATEGIAS")
    print("=" * 60)
    
    try:
        # 1. Conectar a la base de datos
        print("🔌 Paso 1: Conectando a la base de datos...")
        db = PostgresIndicadorDB()
        strategy_service = TradingStrategyService(db)
        print("✅ Conexión exitosa")
        
        # 2. Insertar una estrategia de prueba
        print("\n📝 Paso 2: Insertando estrategia de prueba...")
        strategy_id = strategy_service.save_strategy(
            symbol="BTCUSDT",
            action="LONG",
            confidence=0.85,
            entry_price=45000.0,
            stop_loss=44000.0,
            take_profit=47000.0,
            risk_reward_ratio=2.0,
            justification="RSI oversold + MACD bullish divergence",
            key_factors="Strong support at 44k, volume increasing",
            risk_level="MEDIUM",
            llm_response={"signal": "LONG", "confidence": 0.85},
            market_conditions={"rsi": 25.8, "macd_hist": 3.5}
        )
        print(f"✅ Estrategia creada con ID: {strategy_id}")
        
        # 3. Consultar estrategias activas via API
        print("\n🔍 Paso 3: Consultando estrategias activas via API...")
        response = requests.get("http://localhost:8000/trading-strategies/active")
        if response.status_code == 200:
            strategies = response.json()
            print(f"✅ API respondió correctamente. Estrategias encontradas: {len(strategies)}")
            if strategies:
                strategy = strategies[0]
                print(f"   - ID: {strategy['id']}")
                print(f"   - Símbolo: {strategy['symbol']}")
                print(f"   - Acción: {strategy['action']}")
                print(f"   - Confianza: {strategy['confidence']}")
                print(f"   - Precio entrada: {strategy['entry_price']}")
        else:
            print(f"❌ Error en API: {response.status_code} - {response.text}")
            return False
        
        # 4. Consultar estadísticas
        print("\n📊 Paso 4: Consultando estadísticas...")
        response = requests.get("http://localhost:8000/trading-strategies/stats/summary")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Estadísticas obtenidas:")
            print(f"   - Total estrategias: {stats['total_strategies']}")
            print(f"   - Estrategias activas: {stats['active_strategies']}")
            print(f"   - Estrategias ejecutadas: {stats['executed_strategies']}")
            print(f"   - Tasa de éxito: {stats['success_rate']}%")
        else:
            print(f"❌ Error en estadísticas: {response.status_code} - {response.text}")
            return False
        
        # 5. Verificar health check
        print("\n🏥 Paso 5: Verificando health check...")
        response = requests.get("http://localhost:8000/trading-strategies/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Health check exitoso:")
            print(f"   - Status: {health['status']}")
            print(f"   - DB conectada: {health['database_connected']}")
            print(f"   - Versión: {health['service_version']}")
        else:
            print(f"❌ Error en health check: {response.status_code} - {response.text}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 RESULTADO FINAL: ✅ INTEGRACIÓN EXITOSA")
        print("\n🔧 FUNCIONALIDADES VERIFICADAS:")
        print("   ✅ Conexión a base de datos")
        print("   ✅ Inserción de estrategias")
        print("   ✅ API endpoints funcionando")
        print("   ✅ Consulta de estrategias activas")
        print("   ✅ Estadísticas del sistema")
        print("   ✅ Health check")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en test de integración: {e}")
        print("\n" + "=" * 60)
        print("🏁 RESULTADO FINAL: ❌ INTEGRACIÓN FALLÓ")
        return False

if __name__ == "__main__":
    test_strategy_integration()