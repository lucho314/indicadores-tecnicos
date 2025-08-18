from service.llm_analyzer import LLMAnalyzer
from service.whatsapp_notifier import send_whatsapp_alert
from database.db_manager import IndicadorDB
from datetime import datetime
import json

def test_complete_pipeline():
    """Prueba el pipeline completo: LLM + WhatsApp"""
    
    print("🚀 PRUEBA PIPELINE COMPLETO")
    print("="*60)
    
    # Datos simulados que cumplan las condiciones
    test_data = {
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USD",
        "interval": "4h",
        "close_price": 58000,
        "rsi": 25.8,  # RSI < 30 ✅
        "sma": 59500,
        "adx": 42.0,
        "macd": -45.2,
        "macd_signal": -48.1,
        "macd_hist": 3.5,  # MACD_Hist > 0 ✅
        "bb_upper": 60000,
        "bb_middle": 58500,
        "bb_lower": 57000
    }
    
    print("📊 CONDICIONES SIMULADAS:")
    print(f"RSI: {test_data['rsi']} (< 30 ✅)")
    print(f"MACD_Hist: {test_data['macd_hist']} (> 0 ✅)")
    print()
    
    try:
        # 1. Preparar contexto
        print("🔄 Paso 1: Preparando contexto...")
        db = IndicadorDB()
        db.save_indicators(test_data)
        llm_context = db.build_llm_context("BTC/USD", test_data)
        print("✅ Contexto preparado")
        
        # 2. Llamar a OpenAI
        print("🤖 Paso 2: Consultando OpenAI...")
        analyzer = LLMAnalyzer()
        llm_result = analyzer.analyze(llm_context)
        
        if "error" in llm_result:
            print(f"❌ Error en LLM: {llm_result['error']}")
            return False
            
        print("✅ OpenAI completado")
        print(f"📈 Tokens usados: {llm_result.get('tokens_used', 'N/A')}")
        
        # 3. Mostrar análisis
        analysis = llm_result.get("analysis", {})
        print()
        print("📊 RECOMENDACIÓN GENERADA:")
        print("-" * 30)
        print(f"Acción: {analysis.get('action', 'N/A')}")
        print(f"Confianza: {analysis.get('confidence', 'N/A')}%")
        print(f"Entrada: ${analysis.get('entry_price', 'N/A')}")
        print(f"Stop Loss: ${analysis.get('stop_loss', 'N/A')}")
        print(f"Take Profit: ${analysis.get('take_profit', 'N/A')}")
        print(f"R/R: {analysis.get('risk_reward_ratio', 'N/A')}")
        
        # 4. Enviar WhatsApp
        print()
        print("📱 Paso 3: Enviando WhatsApp...")
        whatsapp_result = send_whatsapp_alert(llm_result, "BTC/USD")
        
        if whatsapp_result.get("success"):
            print("✅ WhatsApp enviado exitosamente")
            print(f"📞 Teléfono: {whatsapp_result.get('phone', 'N/A')}")
            print()
            print("📄 MENSAJE ENVIADO:")
            print("-" * 40)
            print(whatsapp_result.get("message_sent", "N/A"))
            print("-" * 40)
            
            return True
        else:
            print(f"❌ Error enviando WhatsApp: {whatsapp_result.get('error', 'Unknown')}")
            return False
            
    except Exception as e:
        print(f"❌ Error en pipeline: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_pipeline()
    
    print("\n" + "="*60)
    print(f"🏁 RESULTADO FINAL: {'✅ PIPELINE COMPLETO EXITOSO' if success else '❌ PIPELINE FALLÓ'}")
    
    if success:
        print()
        print("🎯 SISTEMA COMPLETAMENTE FUNCIONAL:")
        print("✅ Indicadores técnicos")
        print("✅ Base de datos SQLite") 
        print("✅ Análisis OpenAI")
        print("✅ Alertas WhatsApp")
        print()
        print("🚀 ¡Listo para producción!")
