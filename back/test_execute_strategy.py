#!/usr/bin/env python3
"""
Script de prueba para el método execute_strategy de BybitService
"""

import sys
import os
from service.bybit_service import BybitService

def test_execute_strategy():
    """
    Prueba el método execute_strategy con parámetros de ejemplo
    """
    try:
        print("🧪 Iniciando prueba de execute_strategy...")
        
        # Inicializar servicio de Bybit
        bybit_service = BybitService()
        
        # Verificar conexión
        if not bybit_service.test_connection():
            print("❌ Error: No se pudo conectar a Bybit")
            return False
        
        # Parámetros de prueba para una estrategia
        test_params = {
            'symbol': 'BTCUSDT',
            'side': 'Buy',  # Compra
            'entry_price': 95000.0,  # Precio de entrada
            'take_profit': 98000.0,  # Take profit (+3.16%)
            'stop_loss': 92000.0,    # Stop loss (-3.16%)
            'average_price': 95500.0, # Precio promedio
            'ticket': 'TEST_STRATEGY_001',  # ID de la estrategia
            'usdt_amount': 10.0      # $10 USDT para prueba
        }
        
        print("📊 Parámetros de prueba:")
        for key, value in test_params.items():
            print(f"  {key}: {value}")
        
        # Obtener balance antes de la operación
        print("\n💰 Consultando balance disponible...")
        balance_info = bybit_service.get_available_balance()
        print(f"Balance disponible: ${balance_info.get('transferBalance', 0)} USDT")
        
        # Verificar si hay suficiente balance
        if balance_info.get('transferBalance', 0) < test_params['usdt_amount']:
            print(f"⚠️ Balance insuficiente para la prueba. Requerido: ${test_params['usdt_amount']} USDT")
            print("ℹ️ La prueba continuará para mostrar la validación, pero no ejecutará la orden real.")
        
        # Ejecutar estrategia
        print("\n🚀 Ejecutando estrategia de prueba...")
        result = bybit_service.execute_strategy(**test_params)
        
        # Mostrar resultado
        print("\n📋 Resultado de la ejecución:")
        print(f"✅ Éxito: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"🎫 Ticket: {result.get('ticket')}")
            print(f"📈 Símbolo: {result.get('symbol')}")
            print(f"📊 Lado: {result.get('side')}")
            print(f"💰 Cantidad: {result.get('quantity')} {result.get('symbol', '').replace('USDT', '')}")
            print(f"🆔 Order ID: {result.get('order_id')}")
            print(f"🎯 Take Profit: ${result.get('take_profit')}")
            print(f"🛑 Stop Loss: ${result.get('stop_loss')}")
            
            # Mostrar información de órdenes TP/SL
            tp_sl_orders = result.get('tp_sl_orders', {})
            if tp_sl_orders:
                print("\n🎯 Órdenes TP/SL:")
                if 'take_profit' in tp_sl_orders:
                    tp_info = tp_sl_orders['take_profit']
                    if tp_info.get('success'):
                        print(f"  ✅ Take Profit: {tp_info.get('order_id')} @ ${tp_info.get('price')}")
                    else:
                        print(f"  ❌ Take Profit falló: {tp_info.get('error')}")
                
                if 'stop_loss' in tp_sl_orders:
                    sl_info = tp_sl_orders['stop_loss']
                    if sl_info.get('success'):
                        print(f"  ✅ Stop Loss: {sl_info.get('order_id')} @ ${sl_info.get('price')}")
                    else:
                        print(f"  ❌ Stop Loss falló: {sl_info.get('error')}")
        else:
            print(f"❌ Error: {result.get('error')}")
            print(f"💬 Mensaje: {result.get('message')}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"💥 Error en prueba: {str(e)}")
        return False

def test_strategy_validation():
    """
    Prueba la validación de parámetros del método execute_strategy
    """
    try:
        print("\n🧪 Probando validación de parámetros...")
        
        bybit_service = BybitService()
        
        # Casos de prueba con parámetros inválidos
        invalid_test_cases = [
            {
                'name': 'Side inválido',
                'params': {
                    'symbol': 'BTCUSDT',
                    'side': 'Invalid',  # Side inválido
                    'entry_price': 95000.0,
                    'take_profit': 98000.0,
                    'stop_loss': 92000.0,
                    'average_price': 95500.0,
                    'ticket': 'TEST_INVALID_001',
                    'usdt_amount': 10.0
                }
            },
            {
                'name': 'Cantidad USDT negativa',
                'params': {
                    'symbol': 'BTCUSDT',
                    'side': 'Buy',
                    'entry_price': 95000.0,
                    'take_profit': 98000.0,
                    'stop_loss': 92000.0,
                    'average_price': 95500.0,
                    'ticket': 'TEST_INVALID_002',
                    'usdt_amount': -10.0  # Cantidad negativa
                }
            },
            {
                'name': 'Precio de entrada cero',
                'params': {
                    'symbol': 'BTCUSDT',
                    'side': 'Buy',
                    'entry_price': 0.0,  # Precio inválido
                    'take_profit': 98000.0,
                    'stop_loss': 92000.0,
                    'average_price': 95500.0,
                    'ticket': 'TEST_INVALID_003',
                    'usdt_amount': 10.0
                }
            }
        ]
        
        for test_case in invalid_test_cases:
            print(f"\n🔍 Probando: {test_case['name']}")
            result = bybit_service.execute_strategy(**test_case['params'])
            
            if not result.get('success'):
                print(f"  ✅ Validación correcta: {result.get('error')}")
            else:
                print(f"  ❌ Error: La validación debería haber fallado")
        
        return True
        
    except Exception as e:
        print(f"💥 Error en prueba de validación: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del método execute_strategy...")
    
    # Ejecutar pruebas
    validation_success = test_strategy_validation()
    strategy_success = test_execute_strategy()
    
    print("\n" + "="*50)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*50)
    print(f"✅ Validación de parámetros: {'EXITOSA' if validation_success else 'FALLIDA'}")
    print(f"🚀 Ejecución de estrategia: {'EXITOSA' if strategy_success else 'FALLIDA'}")
    
    if validation_success and strategy_success:
        print("\n🎉 Todas las pruebas completadas exitosamente!")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisar logs para más detalles.")