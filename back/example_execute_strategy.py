#!/usr/bin/env python3
"""
Ejemplo de uso del método execute_strategy de BybitService
"""

from service.bybit_service import BybitService

def example_long_strategy():
    """
    Ejemplo de ejecución de una estrategia LONG (compra)
    """
    try:
        # Inicializar servicio de Bybit
        bybit_service = BybitService()
        
        # Parámetros para estrategia LONG
        strategy_params = {
            'symbol': 'BTCUSDT',           # Par de trading
            'side': 'Buy',                 # Compra (LONG)
            'entry_price': 95000.0,        # Precio de entrada
            'take_profit': 98500.0,        # Take profit (+3.68%)
            'stop_loss': 92000.0,          # Stop loss (-3.16%)
            'average_price': 95750.0,      # Precio promedio esperado
            'ticket': 'LONG_BTC_001',      # ID único de la estrategia
            'usdt_amount': 50.0            # Cantidad a invertir en USDT
        }
        
        print("🚀 Ejecutando estrategia LONG...")
        result = bybit_service.execute_strategy(**strategy_params)
        
        if result['success']:
            print(f"✅ Estrategia ejecutada: {result['message']}")
            print(f"📊 Order ID: {result['order_id']}")
            print(f"💰 Cantidad: {result['quantity']} BTC")
        else:
            print(f"❌ Error: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return None

def example_short_strategy():
    """
    Ejemplo de ejecución de una estrategia SHORT (venta)
    """
    try:
        # Inicializar servicio de Bybit
        bybit_service = BybitService()
        
        # Parámetros para estrategia SHORT
        strategy_params = {
            'symbol': 'BTCUSDT',           # Par de trading
            'side': 'Sell',                # Venta (SHORT)
            'entry_price': 95000.0,        # Precio de entrada
            'take_profit': 91500.0,        # Take profit (-3.68%)
            'stop_loss': 98000.0,          # Stop loss (+3.16%)
            'average_price': 94250.0,      # Precio promedio esperado
            'ticket': 'SHORT_BTC_001',     # ID único de la estrategia
            'usdt_amount': 50.0            # Cantidad a invertir en USDT
        }
        
        print("🚀 Ejecutando estrategia SHORT...")
        result = bybit_service.execute_strategy(**strategy_params)
        
        if result['success']:
            print(f"✅ Estrategia ejecutada: {result['message']}")
            print(f"📊 Order ID: {result['order_id']}")
            print(f"💰 Cantidad: {result['quantity']} BTC")
        else:
            print(f"❌ Error: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return None

def example_from_llm_signal(llm_signal):
    """
    Ejemplo de cómo usar execute_strategy con una señal del LLM
    
    Args:
        llm_signal: Diccionario con la señal del LLM
    """
    try:
        # Inicializar servicio de Bybit
        bybit_service = BybitService()
        
        # Extraer información de la señal del LLM
        action = llm_signal.get('action', 'WAIT')
        confidence = llm_signal.get('confidence', 0)
        current_price = llm_signal.get('current_price', 0)
        
        if action == 'WAIT' or confidence < 70:
            print(f"⏸️ No se ejecuta estrategia: Action={action}, Confidence={confidence}%")
            return None
        
        # Calcular precios basados en la señal
        if action == 'LONG':
            side = 'Buy'
            entry_price = current_price * 1.001  # Entrada ligeramente por encima del precio actual
            take_profit = current_price * 1.035  # +3.5% profit
            stop_loss = current_price * 0.975    # -2.5% loss
        elif action == 'SHORT':
            side = 'Sell'
            entry_price = current_price * 0.999  # Entrada ligeramente por debajo del precio actual
            take_profit = current_price * 0.965  # -3.5% profit (para SHORT)
            stop_loss = current_price * 1.025    # +2.5% loss (para SHORT)
        else:
            print(f"❌ Acción no reconocida: {action}")
            return None
        
        # Calcular cantidad basada en la confianza
        base_amount = 25.0  # Cantidad base en USDT
        confidence_multiplier = confidence / 100.0
        usdt_amount = base_amount * confidence_multiplier
        
        # Parámetros de la estrategia
        strategy_params = {
            'symbol': 'BTCUSDT',
            'side': side,
            'entry_price': round(entry_price, 2),
            'take_profit': round(take_profit, 2),
            'stop_loss': round(stop_loss, 2),
            'average_price': round(current_price, 2),
            'ticket': f'{action}_AUTO_{int(confidence)}',
            'usdt_amount': round(usdt_amount, 2)
        }
        
        print(f"🤖 Ejecutando estrategia automática desde LLM:")
        print(f"   Action: {action}, Confidence: {confidence}%")
        print(f"   Amount: ${usdt_amount} USDT")
        
        result = bybit_service.execute_strategy(**strategy_params)
        
        if result['success']:
            print(f"✅ Estrategia automática ejecutada: {result['message']}")
        else:
            print(f"❌ Error en estrategia automática: {result['error']}")
            
        return result
        
    except Exception as e:
        print(f"💥 Error en estrategia automática: {str(e)}")
        return None

if __name__ == "__main__":
    print("📚 Ejemplos de uso del método execute_strategy")
    print("="*50)
    
    # Ejemplo 1: Estrategia LONG manual
    print("\n1️⃣ Ejemplo de estrategia LONG:")
    # example_long_strategy()
    
    # Ejemplo 2: Estrategia SHORT manual
    print("\n2️⃣ Ejemplo de estrategia SHORT:")
    # example_short_strategy()
    
    # Ejemplo 3: Estrategia automática desde señal LLM
    print("\n3️⃣ Ejemplo de estrategia automática desde LLM:")
    
    # Simular señal del LLM
    mock_llm_signal = {
        'action': 'LONG',
        'confidence': 85,
        'current_price': 95000.0,
        'reasoning': 'Indicadores técnicos favorables para compra'
    }
    
    # example_from_llm_signal(mock_llm_signal)
    
    print("\n📝 Nota: Los ejemplos están comentados para evitar ejecuciones accidentales.")
    print("💡 Descomenta las líneas para ejecutar los ejemplos reales.")