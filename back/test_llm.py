from service.llm_analyzer import LLMAnalyzer
from database.db_manager import IndicadorDB
from datetime import datetime
import json

def test_llm_analyzer():
    """Prueba el analizador LLM con datos simulados"""
    
    # Datos simulados que cumplan las condiciones
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USD",
        "interval": "4h",
        "close_price": 58000,
        "rsi": 28.5,  # RSI < 30 ✅
        "sma": 59500,
        "adx": 35.0,
        "macd": -45.2,
        "macd_signal": -48.1,
        "macd_hist": 2.9,  # MACD_Hist > 0 ✅
        "bb_upper": 60000,
        "bb_middle": 58500,
        "bb_lower": 57000
    }
    
    # Simular contexto como lo haría main.py
    db = IndicadorDB()
    db.save_indicators(test_data)
    
    llm_context = db.build_llm_context("BTC/USD", test_data)
    
    print("🎯 PROBANDO ANALIZADOR LLM")
    print("="*50)
    print(f"RSI: {test_data['rsi']} (< 30 ✅)")
    print(f"MACD_Hist: {test_data['macd_hist']} (> 0 ✅)")
    print()
    
    try:
        print("🤖 Llamando a OpenAI...")
        analyzer = LLMAnalyzer()
        result = analyzer.analyze(llm_context)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Análisis completado!")
            print(f"Tokens usados: {result.get('tokens_used', 'N/A')}")
            print()
            print("📊 RECOMENDACIÓN DEL LLM:")
            print("="*50)
            
            analysis = result.get("analysis", {})
            print(f"Acción: {analysis.get('action', 'N/A')}")
            print(f"Confianza: {analysis.get('confidence', 'N/A')}%")
            print(f"Precio Entrada: ${analysis.get('entry_price', 'N/A')}")
            print(f"Stop Loss: ${analysis.get('stop_loss', 'N/A')}")
            print(f"Take Profit: ${analysis.get('take_profit', 'N/A')}")
            print(f"R/R Ratio: {analysis.get('risk_reward_ratio', 'N/A')}")
            print(f"Factores Clave: {analysis.get('key_factors', [])}")
            print()
            print("ANÁLISIS DETALLADO:")
            print(analysis.get('analysis', 'N/A'))
            
    except Exception as e:
        print(f"❌ Error ejecutando prueba: {e}")
        print("Verifica que OPENAI_API_KEY esté configurada")

if __name__ == "__main__":
    test_llm_analyzer()
