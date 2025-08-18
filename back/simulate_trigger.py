from database.db_manager import IndicadorDB
from datetime import datetime
import json

# Simular datos que cumplan las condiciones
def simulate_conditions():
    db = IndicadorDB()
    
    # Datos que cumplan RSI < 30
    rsi_trigger_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USD",
        "interval": "4h",
        "close_price": 58000,
        "rsi": 25.5,  # RSI < 30 ✅
        "sma": 59500,
        "adx": 35.0,
        "macd": -45.2,
        "macd_signal": -48.1,
        "macd_hist": 2.9,  # MACD_Hist > 0 ✅
        "bb_upper": 60000,
        "bb_middle": 58500,
        "bb_lower": 57000
    }
    
    # Guardar datos simulados
    db.save_indicators(rsi_trigger_data)
    
    # Construir contexto como lo haría el main
    llm_context = db.build_llm_context("BTC/USD", rsi_trigger_data)
    
    print("🎯 DATOS SIMULADOS QUE CUMPLEN CONDICIONES")
    print("="*50)
    print(f"RSI: {rsi_trigger_data['rsi']} (< 30 ✅)")
    print(f"MACD_Hist: {rsi_trigger_data['macd_hist']} (> 0 ✅)")
    print()
    print("📊 CONTEXTO PARA LLM:")
    print(json.dumps(llm_context, indent=2))

if __name__ == "__main__":
    simulate_conditions()
