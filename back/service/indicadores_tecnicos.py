from typing import Dict, Any
from config import SYMBOL, INTERVAL
from service.indicators_engine import IndicatorsEngine



def obtener_indicadores(symbol: str = "BTCUSDT", interval: str = "240") -> Dict[str, Any]:
    """
    Nueva función principal que usa el sistema reingeniado de indicadores
    Obtiene datos directamente de Bybit y calcula indicadores con pandas_ta
    
    Args:
        symbol: Par de trading (ej: BTCUSDT)
        interval: Intervalo en minutos (240=4h, 60=1h)
        
    Returns:
        Diccionario con todos los indicadores técnicos calculados
    """
    try:
        # Inicializar el motor de indicadores
        engine = IndicatorsEngine()
        
        # Calcular indicadores directamente con el nuevo sistema
        indicators = engine.calculate_current_indicators(symbol=symbol, interval=interval)
        
        if indicators:
            
            # Adaptar formato para compatibilidad con el sistema anterior
            formatted_result = {
                "symbol": symbol,
                "interval": interval,
                "timestamp": indicators.get("timestamp", ""),
                "price": indicators.get("close_price", 0),
                "close_price": indicators.get("close_price", 0),
                
                # Indicadores principales
                "rsi": indicators.get("rsi14", 0),
                "rsi14": indicators.get("rsi14", 0),
                "ema20": indicators.get("ema20", 0),
                "ema200": indicators.get("ema200", 0),
                "sma": indicators.get("sma20", 0),
                "sma20": indicators.get("sma20", 0),
                "sma50": indicators.get("sma50", 0),
                "sma200": indicators.get("sma200", 0),
                
                # MACD
                "macd": indicators.get("macd", 0),
                "macd_signal": indicators.get("macd_signal", 0),
                "macd_hist": indicators.get("macd_hist", 0),
                "macd_histogram": indicators.get("macd_hist", 0),
                
                # Bollinger Bands
                "bb_upper": indicators.get("bb_upper", 0),
                "bb_middle": indicators.get("bb_middle", 0),
                "bb_lower": indicators.get("bb_lower", 0),
                
                # Otros indicadores
                "adx": indicators.get("adx14", 0),
                "adx14": indicators.get("adx14", 0),
                "atr14": indicators.get("atr14", 0),
                "obv": indicators.get("obv", 0),
                
                # Metadatos
                "source": "bybit_reengineered",
                "calculation_time": 0,
                "system_status": {"status": "active"},
                "errors": {}
            }
            
            return formatted_result
            
        else:
            return {
                "symbol": symbol,
                "interval": interval,
                "errors": {"calculation": "No se pudieron calcular los indicadores"}
            }
            
    except Exception as e:
        print(f"❌ Error en sistema de indicadores: {e}")
        return {
            "symbol": symbol,
            "interval": interval,
            "errors": {"system": str(e)}
        }

if __name__ == "__main__":
    # Probar el nuevo sistema
    print("🧪 Probando nuevo sistema de indicadores...")
    data = obtener_indicadores("BTCUSDT", "240")
    print("📊 Resultado:")
    for key, value in data.items():
        if key not in ["errors", "system_status"]:
            print(f"  {key}: {value}")
    
    if data.get("errors"):
        print(f"❌ Errores: {data['errors']}")
