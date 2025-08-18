from service.whatsapp_notifier import WhatsAppNotifier
import json

def test_whatsapp_format():
    """Prueba el formato del mensaje de WhatsApp"""
    
    # Datos simulados de respuesta del LLM
    mock_llm_result = {
        "llm_called": True,
        "analysis": {
            "action": "LONG",
            "confidence": 78,
            "entry_price": 58500,
            "stop_loss": 56930,
            "take_profit": 61000,
            "risk_reward_ratio": 1.85,
            "key_factors": [
                "RSI en sobreventa sugiriendo reversión alcista",
                "MACD cruce alcista reciente", 
                "ADX muestra fuerte tendencia",
                "SMA actuando como soporte",
                "Contracción de las Bollinger Bands indicando posible expansión de volatilidad"
            ],
            "timeframe_outlook": "4-12h",
            "risk_level": "MEDIUM"
        }
    }
    
    try:
        notifier = WhatsAppNotifier()
        message = notifier.format_trading_alert(mock_llm_result, "BTC/USD")
        
        print("📱 PREVIEW DEL MENSAJE WHATSAPP:")
        print("="*50)
        print(message)
        print("="*50)
        print(f"Longitud: {len(message)} caracteres")
        
        # También mostrar cómo se vería la URL (sin enviar)
        from urllib.parse import quote
        encoded_message = quote(message)
        print(f"\n🔗 URL generada (truncada): ...text={encoded_message[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Nota: Es normal si no tienes CALLMEBOT_PHONE/APIKEY configurados")

if __name__ == "__main__":
    test_whatsapp_format()
