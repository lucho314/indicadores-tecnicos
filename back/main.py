import sys
import argparse
import os
from datetime import datetime
from typing import Dict, Any, Optional
from service.indicadores_tecnicos import obtener_indicadores
from service.klines_service import KlinesService
from service.technical_indicators import TechnicalIndicatorsCalculator
from service.llm_analyzer import llamar_llm
from service.whatsapp_notifier import send_whatsapp_alert
from service.bybit_service import BybitService
from service.trading_strategy_service import TradingStrategyService
from database.postgres_db_manager import PostgresIndicadorDB

def ensure_database_setup() -> bool:
    """
    Verifica y configura automáticamente la base de datos si es necesario
    
    Returns:
        bool: True si la base de datos está lista, False si hay errores
    """
    try:
        print("🔍 Verificando configuración de base de datos...")
        
        # Inicializar conexión
        db_manager = PostgresIndicadorDB()
        
        # Verificar si la tabla klines existe
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'klines'
                    )
                """)
                klines_exists = cur.fetchone()[0]
                
                if not klines_exists:
                    print("⚠️ Tabla 'klines' no encontrada. Ejecutando migración...")
                    
                    # Ejecutar migración
                    script_path = os.path.join(os.path.dirname(__file__), "database", "create_klines_table.sql")
                    
                    if not os.path.exists(script_path):
                        print(f"❌ Script de migración no encontrado: {script_path}")
                        return False
                        
                    with open(script_path, 'r', encoding='utf-8') as f:
                        sql_script = f.read()
                        
                    cur.execute(sql_script)
                    conn.commit()
                    
                    print("✅ Migración de tabla 'klines' completada")
                else:
                    print("✅ Tabla 'klines' ya existe")
                    
                # Verificar tabla indicadores
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'indicadores'
                    )
                """)
                indicadores_exists = cur.fetchone()[0]
                
                if indicadores_exists:
                    print("✅ Tabla 'indicadores' disponible")
                else:
                    print("⚠️ Tabla 'indicadores' no encontrada (se creará automáticamente si es necesario)")
                    
                # Verificar tabla trading_strategies
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'trading_strategies'
                    )
                """)
                trading_strategies_exists = cur.fetchone()[0]
                
                if not trading_strategies_exists:
                    print("⚠️ Tabla 'trading_strategies' no encontrada. Ejecutando migración...")
                    
                    # Ejecutar migración
                    script_path = os.path.join(os.path.dirname(__file__), "database", "create_trading_strategies_table.sql")
                    
                    if not os.path.exists(script_path):
                        print(f"❌ Script de migración no encontrado: {script_path}")
                        return False
                        
                    with open(script_path, 'r', encoding='utf-8') as f:
                        sql_script = f.read()
                        
                    cur.execute(sql_script)
                    conn.commit()
                    
                    print("✅ Migración de tabla 'trading_strategies' completada")
                else:
                    print("✅ Tabla 'trading_strategies' ya existe")
                    
        print("✅ Verificación de base de datos completada")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        print("💡 Sugerencia: Ejecuta 'python setup_new_indicators.py' manualmente")
        return False

def save_llm_strategy(
    strategy_service: TradingStrategyService,
    llm_result: Dict[str, Any],
    symbol: str,
    current_price: float,
    market_conditions: Dict[str, Any]
) -> Optional[int]:
    """
    Extrae y guarda la estrategia del LLM en la base de datos
    
    Args:
        strategy_service: Servicio de estrategias
        llm_result: Resultado del análisis del LLM
        symbol: Símbolo del activo
        current_price: Precio actual del activo
        market_conditions: Condiciones del mercado
        
    Returns:
        ID de la estrategia guardada o None si no se guardó
    """
    try:
        analysis = llm_result.get("analysis", {})
        action = analysis.get("action", "WAIT")
        
        # Solo guardar estrategias SHORT o LONG
        if action not in ["SHORT", "LONG"]:
            return None
        
        # Extraer datos de la estrategia
        confidence = analysis.get("confidence", 0)
        entry_price = analysis.get("entry_price", current_price)
        stop_loss = analysis.get("stop_loss")
        take_profit = analysis.get("take_profit")
        risk_reward_ratio = analysis.get("risk_reward_ratio")
        justification = analysis.get("justification", "")
        key_factors = analysis.get("key_factors", "")
        risk_level = analysis.get("risk_level", "MEDIUM")
        
        # Preparar respuesta completa del LLM
        llm_response = {
            "model_used": llm_result.get("model_used"),
            "tokens_used": llm_result.get("tokens_used"),
            "timestamp": llm_result.get("timestamp"),
            "analysis": analysis,
            "raw_response": llm_result.get("raw_response")
        }
        
        # Guardar estrategia
        strategy_id = strategy_service.save_strategy(
            symbol=symbol,
            action=action,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward_ratio,
            justification=justification,
            key_factors=key_factors,
            risk_level=risk_level,
            llm_response=llm_response,
            market_conditions=market_conditions
        )
        
        print(f"✅ Estrategia {action} guardada con ID: {strategy_id}")
        print(f"   Confianza: {confidence}%, Precio entrada: ${entry_price}")
        if stop_loss:
            print(f"   Stop Loss: ${stop_loss}")
        if take_profit:
            print(f"   Take Profit: ${take_profit}")
        if risk_reward_ratio:
            print(f"   R/R Ratio: {risk_reward_ratio}")
        
        return strategy_id
        
    except Exception as e:
        print(f"❌ Error guardando estrategia del LLM: {e}")
        return None

def analyze_trading_signals(indicators: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análisis avanzado de señales de trading usando múltiples indicadores técnicos
    
    Args:
        indicators: Diccionario con todos los indicadores técnicos
        
    Returns:
        Dict con análisis de señales, fuerza y dirección
    """
    signals = []
    strength = 0.0
    direction = "NEUTRAL"
    
    # Obtener valores con validación
    rsi = indicators.get("rsi")
    macd = indicators.get("macd")
    macd_signal = indicators.get("macd_signal")
    macd_hist = indicators.get("macd_hist")
    ema20 = indicators.get("ema20")
    ema200 = indicators.get("ema200")
    sma20 = indicators.get("sma20")
    sma50 = indicators.get("sma50")
    sma200 = indicators.get("sma200")
    bb_upper = indicators.get("bb_upper")
    bb_middle = indicators.get("bb_middle")
    bb_lower = indicators.get("bb_lower")
    adx = indicators.get("adx")
    atr14 = indicators.get("atr14")
    obv = indicators.get("obv")
    price = indicators.get("price")
    
    # 1. Análisis RSI (Peso: 2.0)
    if rsi is not None:
        if rsi < 25:  # Sobreventa extrema
            signals.append("RSI sobreventa extrema")
            strength += 2.0
            direction = "BULLISH"
        elif rsi < 35:  # Sobreventa
            signals.append("RSI sobreventa")
            strength += 1.5
            direction = "BULLISH"
        elif rsi > 75:  # Sobrecompra extrema
            signals.append("RSI sobrecompra extrema")
            strength += 2.0
            direction = "BEARISH"
        elif rsi > 65:  # Sobrecompra
            signals.append("RSI sobrecompra")
            strength += 1.5
            direction = "BEARISH"
    
    # 2. Análisis MACD (Peso: 1.5)
    if all(v is not None for v in [macd, macd_signal, macd_hist]):
        if macd > macd_signal and macd_hist > 0:
            signals.append("MACD bullish")
            strength += 1.5
            if direction != "BEARISH":
                direction = "BULLISH"
        elif macd < macd_signal and macd_hist < 0:
            signals.append("MACD bearish")
            strength += 1.5
            if direction != "BULLISH":
                direction = "BEARISH"
    
    # 3. Análisis de Medias Móviles (Peso: 1.5)
    if all(v is not None for v in [price, ema20, ema200, sma50, sma200]):
        # Tendencia alcista: precio > EMA20 > EMA200 y precio > SMA50 > SMA200
        if price > ema20 > ema200 and price > sma50 > sma200:
            signals.append("Tendencia alcista fuerte")
            strength += 1.5
            if direction != "BEARISH":
                direction = "BULLISH"
        # Tendencia bajista: precio < EMA20 < EMA200 y precio < SMA50 < SMA200
        elif price < ema20 < ema200 and price < sma50 < sma200:
            signals.append("Tendencia bajista fuerte")
            strength += 1.5
            if direction != "BULLISH":
                direction = "BEARISH"
        # Cruce alcista: precio cruza por encima de medias importantes
        elif price > ema20 and ema20 > sma50:
            signals.append("Cruce alcista de medias")
            strength += 1.0
            if direction != "BEARISH":
                direction = "BULLISH"
    
    # 4. Análisis Bollinger Bands (Peso: 1.0)
    if all(v is not None for v in [price, bb_upper, bb_middle, bb_lower]):
        bb_position = (price - bb_lower) / (bb_upper - bb_lower)
        if bb_position < 0.1:  # Cerca del límite inferior
            signals.append("Precio en banda inferior BB")
            strength += 1.0
            if direction != "BEARISH":
                direction = "BULLISH"
        elif bb_position > 0.9:  # Cerca del límite superior
            signals.append("Precio en banda superior BB")
            strength += 1.0
            if direction != "BULLISH":
                direction = "BEARISH"
    
    # 5. Análisis ADX - Fuerza de tendencia (Peso: 1.0)
    if adx is not None:
        if adx > 40:  # Tendencia muy fuerte
            signals.append(f"Tendencia muy fuerte (ADX: {adx:.1f})")
            strength += 1.0
        elif adx > 25:  # Tendencia fuerte
            signals.append(f"Tendencia fuerte (ADX: {adx:.1f})")
            strength += 0.5
    
    # 6. Análisis de volatilidad ATR (Peso: 0.5)
    if atr14 is not None and price is not None:
        atr_percentage = (atr14 / price) * 100
        if atr_percentage > 5:  # Alta volatilidad
            signals.append(f"Alta volatilidad (ATR: {atr_percentage:.1f}%)")
            strength += 0.5
    
    # 7. Confluencia de señales - Bonus
    bullish_signals = sum(1 for s in signals if any(word in s.lower() for word in ["bullish", "alcista", "sobreventa", "inferior"]))
    bearish_signals = sum(1 for s in signals if any(word in s.lower() for word in ["bearish", "bajista", "sobrecompra", "superior"]))
    
    if bullish_signals >= 3:
        signals.append("Confluencia bullish")
        strength += 1.0
        direction = "BULLISH"
    elif bearish_signals >= 3:
        signals.append("Confluencia bearish")
        strength += 1.0
        direction = "BEARISH"
    
    # Normalizar fuerza a escala 0-10
    strength = min(strength, 10.0)
    
    # Determinar si se debe analizar (umbral de fuerza >= 3.0)
    should_analyze = strength >= 2.0
    
    return {
        "should_analyze": should_analyze,
        "strength": strength,
        "direction": direction,
        "signals": signals,
        "summary": f"{len(signals)} señales detectadas" if signals else "Sin señales significativas",
        "bullish_count": bullish_signals,
        "bearish_count": bearish_signals
    }

def main(symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Función principal del análisis de indicadores
    
    Args:
        symbol: Símbolo de la criptomoneda (opcional)
    
    Returns:
        Dict con el resultado del análisis
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Iniciando análisis de indicadores...")
    
    # Verificar y configurar base de datos automáticamente
    if not ensure_database_setup():
        return {
            "timestamp": timestamp,
            "symbol": "N/A",
            "interval": "N/A",
            "conditions_met": False,
            "llm_called": False,
            "errors": "Error en configuración de base de datos"
        }
    
    # Inicializar base de datos PostgreSQL
    db = PostgresIndicadorDB()
    
    # Inicializar servicio de estrategias
    strategy_service = TradingStrategyService(db)
    
    if symbol:
        print(f"[{timestamp}] Símbolo recibido por parámetro: {symbol}")
    
    # Obtener indicadores directamente de Bybit (datos frescos)
    print(f"[{timestamp}] Obteniendo indicadores con datos frescos de Bybit...")
    
    # Usar símbolo por defecto si no se proporciona
    target_symbol = symbol if symbol else "BTCUSDT"
    target_interval = "240"  # 4 horas por defecto
    
    try:
        # Inicializar servicios para obtener datos frescos
        klines_service = KlinesService(db)
        calculator = TechnicalIndicatorsCalculator()
        
        # Obtener las últimas 1000 velas directamente de Bybit para análisis más preciso
        print(f"[{timestamp}] 📥 Obteniendo datos frescos de Bybit para {target_symbol}...")
        fresh_klines = klines_service.fetch_klines_from_api(
            symbol=target_symbol,
            interval=target_interval,
            limit=1000
        )
        
        if not fresh_klines or len(fresh_klines) < 50:
            print(f"[{timestamp}] ❌ Insuficientes datos de Bybit: {len(fresh_klines) if fresh_klines else 0}")
            # Fallback al método anterior
            data = obtener_indicadores(target_symbol)
        else:
            print(f"[{timestamp}] ✅ Obtenidas {len(fresh_klines)} velas frescas de Bybit para análisis completo")
            
            # Calcular indicadores con datos frescos
            indicators = calculator.calculate_all_indicators(fresh_klines)
            
            if indicators:
                # Adaptar formato para compatibilidad
                data = {
                    "symbol": target_symbol,
                    "interval": target_interval,
                    "timestamp": indicators.get("timestamp", timestamp),
                    "price": indicators.get("close_price", 0),
                    "close_price": indicators.get("close_price", 0),
                    "rsi": indicators.get("rsi14", 0),
                    "rsi14": indicators.get("rsi14", 0),
                    "ema20": indicators.get("ema20", 0),
                    "ema200": indicators.get("ema200", 0),
                    "sma": indicators.get("sma20", 0),
                    "sma20": indicators.get("sma20", 0),
                    "sma50": indicators.get("sma50", 0),
                    "sma200": indicators.get("sma200", 0),
                    "macd": indicators.get("macd", 0),
                    "macd_signal": indicators.get("macd_signal", 0),
                    "macd_hist": indicators.get("macd_hist", 0),
                    "bb_upper": indicators.get("bb_upper", 0),
                    "bb_middle": indicators.get("bb_middle", 0),
                    "bb_lower": indicators.get("bb_lower", 0),
                    "adx": indicators.get("adx14", 0),
                    "atr14": indicators.get("atr14", 0),
                    "obv": indicators.get("obv", 0),
                    "source": "bybit_fresh_data",
                    "errors": {}
                }
                print(f"[{timestamp}] ✅ Indicadores calculados con datos frescos - Precio: ${data['close_price']:.2f}")
            else:
                print(f"[{timestamp}] ❌ Error calculando indicadores con datos frescos")
                # Fallback al método anterior
                data = obtener_indicadores(target_symbol)
                
    except Exception as e:
        print(f"[{timestamp}] ❌ Error obteniendo datos frescos: {e}")
        # Fallback al método anterior
        data = obtener_indicadores(target_symbol)
    
    # Inicializar servicio de Bybit para consultar posiciones
    bybit_service = None
    current_position = None
    try:
        bybit_service = BybitService()
        # Convertir símbolo para Bybit (BTC/USD -> BTCUSDT)
        original_symbol = data.get("symbol", "BTC/USD")
        print(f"[{timestamp}] 🔍 Símbolo original: '{original_symbol}'")
        if "/" in original_symbol:
            # Formato BTC/USD -> BTCUSDT
            symbol_base = original_symbol.replace("/", "")
            bybit_symbol = symbol_base + "T"
            print(f"[{timestamp}] 🔄 Convertido de {original_symbol} a {bybit_symbol}")
        else:
            # Ya está en formato BTCUSDT, no agregar T adicional si ya termina en T
            if original_symbol.endswith("T"):
                bybit_symbol = original_symbol
                print(f"[{timestamp}] ✅ Usando símbolo original (ya termina en T): {bybit_symbol}")
            else:
                bybit_symbol = original_symbol + "T"
                print(f"[{timestamp}] 🔄 Agregando T al símbolo: {bybit_symbol}")
        current_position = bybit_service.get_open_position(bybit_symbol)
        if current_position:
            print(f"[{timestamp}] ✅ Posición activa encontrada en Bybit: {bybit_symbol}")
        else:
            print(f"[{timestamp}] ℹ️ No hay posiciones activas en Bybit para {bybit_symbol}")
    except Exception as e:
        print(f"[{timestamp}] ⚠️ Error consultando Bybit: {e}")
        current_position = None
    
    result = {
        "timestamp": timestamp,
        "symbol": data.get("symbol", "N/A"),
        "interval": data.get("interval", "N/A"),
        "conditions_met": False,
        "llm_called": False,
        "errors": None
    }
    
    # Verificar si hay errores
    if data.get("errors") and len(data.get("errors", {})) > 0:
        error_msg = f"Error al obtener indicadores: {data['errors']}"
        print(f"[{timestamp}] {error_msg}")
        result["errors"] = data["errors"]
        return result
    
    # Obtener precio actual en tiempo real de Bybit ANTES de procesar indicadores
    current_price = data.get("close_price", data.get("price", 0))  # Precio por defecto de indicadores
    if bybit_service:
        try:
            # Convertir símbolo para Bybit (BTC/USD -> BTCUSDT)
            original_symbol = data.get("symbol", "BTC/USD")
            print(f"[{timestamp}] 🔍 Símbolo original para precio: '{original_symbol}'")
            if "/" in original_symbol:
                # Formato BTC/USD -> BTCUSDT
                symbol_base = original_symbol.replace("/", "")
                bybit_symbol = symbol_base + "T"
                print(f"[{timestamp}] 🔄 Convertido para precio de {original_symbol} a {bybit_symbol}")
            else:
                # Ya está en formato BTCUSDT, no agregar T adicional si ya termina en T
                if original_symbol.endswith("T"):
                    bybit_symbol = original_symbol
                    print(f"[{timestamp}] ✅ Usando símbolo original para precio (ya termina en T): {bybit_symbol}")
                else:
                    bybit_symbol = original_symbol + "T"
                    print(f"[{timestamp}] 🔄 Agregando T al símbolo para precio: {bybit_symbol}")
            real_time_price = bybit_service.get_price(bybit_symbol)
            if real_time_price:
                current_price = real_time_price
                print(f"[{timestamp}] 💰 Precio actual en tiempo real obtenido: ${current_price}")
            else:
                print(f"[{timestamp}] ⚠️ No se pudo obtener precio en tiempo real, usando precio de indicadores: ${current_price}")
        except Exception as e:
            print(f"[{timestamp}] ❌ Error obteniendo precio en tiempo real: {e}")
            print(f"[{timestamp}] 🔄 Usando precio de indicadores: ${current_price}")
    
    # Obtener todos los indicadores con manejo de None y precio actualizado
    indicators = {
        "rsi": data.get("rsi"),
        "macd": data.get("macd"),
        "macd_signal": data.get("macd_signal"),
        "macd_hist": data.get("macd_hist"),
        "ema20": data.get("ema20"),
        "ema200": data.get("ema200"),
        "sma20": data.get("sma20"),
        "sma50": data.get("sma50"),
        "sma200": data.get("sma200"),
        "bb_upper": data.get("bb_upper"),
        "bb_middle": data.get("bb_middle"),
        "bb_lower": data.get("bb_lower"),
        "adx": data.get("adx"),
        "atr14": data.get("atr14"),
        "obv": data.get("obv"),
        "price": current_price  # Usar el precio en tiempo real
    }
    
    # Agregar timestamp y guardar en BD con precio actualizado
    data["timestamp"] = timestamp
    data["close_price"] = current_price  # Guardar el precio en tiempo real en la BD
    
    # Inicialmente la señal es False
    signal_active = False
    
    # Guardar en base de datos (sin señal inicialmente)
    if db.save_indicators(data, signal=signal_active):
        print(f"[{timestamp}] Datos guardados en BD exitosamente")
    else:
        print(f"[{timestamp}] ⚠️ Error guardando en BD")
    
    # Actualizar resultado con todos los indicadores
    result.update(indicators)
    
    # Análisis avanzado de señales usando múltiples indicadores
    signal_analysis = analyze_trading_signals(indicators)
    has_position = current_position is not None
    
    # Determinar si llamar al LLM basado en análisis avanzado
    should_call_llm = signal_analysis["should_analyze"] or has_position
    
    # Agregar información del análisis al resultado
    result.update({
        "signal_analysis": signal_analysis,
        "signal_strength": signal_analysis["strength"],
        "signal_direction": signal_analysis["direction"]
    })
    
    if should_call_llm:
        if has_position:
            print(f"[{timestamp}] POSICIÓN ACTIVA DETECTADA: Llamando LLM para gestión de posición")
            print(f"[{timestamp}] Posición: {current_position.get('side', 'N/A')} {current_position.get('size', 'N/A')} @ {current_position.get('avgPrice', 'N/A')}")
        else:
            print(f"[{timestamp}] SEÑALES TÉCNICAS DETECTADAS: {signal_analysis['summary']}")
            print(f"[{timestamp}] Fuerza de señal: {signal_analysis['strength']:.2f}/10")
            print(f"[{timestamp}] Dirección: {signal_analysis['direction']}")
        
        print(f"[{timestamp}] Indicadores clave: RSI={indicators['rsi']:.2f}, MACD_Hist={indicators['macd_hist']:.4f}, ADX={indicators['adx']:.2f}" if all(v is not None for v in [indicators['rsi'], indicators['macd_hist'], indicators['adx']]) else f"[{timestamp}] Algunos indicadores no disponibles")
        
        # Construir contexto para LLM
        historical_context = db.build_context_for_llm(data.get("symbol", "N/A"), data)
        
        # Crear contexto estructurado para el LLM incluyendo posición actual
        llm_context = {
            "latest": data,
            "historical_summary": historical_context,
            "symbol": data.get("symbol", "N/A"),
            "timestamp": timestamp,
            "current_position": current_position,  # Nueva información de posición
            "has_position": has_position,
            "bybit_symbol": bybit_symbol if bybit_service else None
        }
        
        # Llamar a LLM con contexto completo
        llm_result = llamar_llm(llm_context)
        
        result.update({
            "conditions_met": True,
            "llm_called": True,
            "llm_result": llm_result,
            "has_position": has_position,
            "current_position": current_position,
            "bybit_symbol": bybit_symbol if bybit_service else None
        })
        
        if llm_result.get("llm_called") and not llm_result.get("error"):
            print(f"[{timestamp}] LLM ejecutado exitosamente")
            
            # Verificar si hay una señal activa (acción != 'WAIT')
            analysis = llm_result.get("analysis", {})
            action = analysis.get("action", "WAIT")
            
            # Guardar estrategia del LLM si es SHORT o LONG
            strategy_id = None
            if action in ["SHORT", "LONG"]:
                # Preparar condiciones del mercado
                market_conditions = {
                    "rsi": indicators.get("rsi"),
                    "macd_hist": indicators.get("macd_hist"),
                    "adx": indicators.get("adx"),
                    "ema20": indicators.get("ema20"),
                    "ema200": indicators.get("ema200"),
                    "bb_upper": indicators.get("bb_upper"),
                    "bb_lower": indicators.get("bb_lower"),
                    "atr14": indicators.get("atr14"),
                    "signal_strength": signal_analysis.get("strength"),
                    "signal_direction": signal_analysis.get("direction"),
                    "has_position": has_position,
                    "current_position": current_position
                }
                
                # El precio actual ya se obtuvo al principio del proceso
                current_price = indicators.get("price", 0)  # Ya contiene el precio en tiempo real
                
                strategy_id = save_llm_strategy(
                    strategy_service=strategy_service,
                    llm_result=llm_result,
                    symbol=data.get("symbol", "N/A"),
                    current_price=current_price,
                    market_conditions=market_conditions
                )
            
            if action and action != "WAIT":
                signal_active = True
                print(f"[{timestamp}] ✅ SEÑAL ACTIVA: {action}")
                
                # Actualizar la base de datos con la señal activa
                try:
                    with db.get_connection() as conn:
                        with conn.cursor() as cur:
                            # Buscar el registro más reciente para este símbolo y actualizarlo
                            cur.execute("""
                                UPDATE indicadores 
                                SET signal = %s 
                                WHERE symbol = %s AND timestamp = %s
                            """, (True, data.get("symbol", "N/A"), datetime.fromisoformat(timestamp.replace('T', ' ').replace('Z', ''))))
                            conn.commit()
                            print(f"[{timestamp}] ✅ Señal actualizada en BD")
                except Exception as e:
                    print(f"[{timestamp}] ⚠️ Error actualizando señal en BD: {e}")
            else:
                print(f"[{timestamp}] No hay señal activa (acción: {action})")
            
            # Agregar ID de estrategia al resultado
            if strategy_id:
                result["strategy_id"] = strategy_id
            
            # Enviar alerta por WhatsApp solo si hay señal fuerte o posición activa
            if signal_active or has_position or signal_analysis["strength"] >= 5.0:
                print(f"[{timestamp}] Enviando alerta por WhatsApp...")
                whatsapp_result = send_whatsapp_alert(llm_result, data.get("symbol", "N/A"))
                
                result["whatsapp_result"] = whatsapp_result
                
                if whatsapp_result.get("success"):
                    print(f"[{timestamp}] ALERTA WhatsApp enviada exitosamente")
                else:
                    print(f"[{timestamp}] ERROR enviando WhatsApp: {whatsapp_result.get('error', 'Unknown')}")
            else:
                print(f"[{timestamp}] No se envía WhatsApp (señal débil o sin posición)")
                
            result["signal_active"] = signal_active
            result["action"] = action
            
        else:
            print(f"[{timestamp}] ERROR en LLM: {llm_result.get('error', 'Unknown')}")
    else:
        if has_position:
            print(f"[{timestamp}] Hay posición activa pero no se pudo llamar al LLM por error en Bybit")
        else:
            print(f"[{timestamp}] Señales insuficientes para análisis. Fuerza: {signal_analysis['strength']:.2f}/10")
        print(f"[{timestamp}] Resumen: {signal_analysis['summary']}")
        
        # Agregar información de posición al resultado aunque no se llame al LLM
        result.update({
            "has_position": has_position,
            "current_position": current_position,
            "bybit_symbol": bybit_symbol if bybit_service else None
        })
    
    # Limpiar datos antiguos ocasionalmente
    if timestamp.endswith("00:00"):  # Una vez por hora
        db.cleanup_old_data(30)
        print(f"[{timestamp}] Limpieza de datos antiguos completada")
    
    print(f"[{timestamp}] Análisis completado")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análisis de indicadores técnicos")
    parser.add_argument("--symbol", "-s", type=str, help="Símbolo de la criptomoneda (ej: BTC/USD)")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    
    args = parser.parse_args()
    
    result = main(args.symbol)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*50}")
        print("RESUMEN DEL ANÁLISIS")
        print(f"{'='*50}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Símbolo: {result['symbol']}")
        print(f"Condiciones cumplidas: {'SI' if result['conditions_met'] else 'NO'}")
        print(f"LLM llamado: {'SI' if result['llm_called'] else 'NO'}")
        if result['errors']:
            print(f"Errores: {result['errors']}")
