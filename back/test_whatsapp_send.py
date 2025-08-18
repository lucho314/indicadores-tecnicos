import sys
from datetime import datetime
from service.whatsapp_notifier import send_whatsapp_alert

def test_whatsapp_send():
    """Prueba real de envío de WhatsApp"""
    
    print("🧪 PRUEBA DE ENVÍO WHATSAPP")
    print("="*50)
    
    # Datos simulados de respuesta del LLM para prueba
    mock_llm_result = {
        "llm_called": True,
        "analysis": {
            "action": "LONG",
            "confidence": 85,
            "entry_price": 58500,
            "stop_loss": 56930,
            "take_profit": 61000,
            "risk_reward_ratio": 1.85,
            "key_factors": [
                "RSI en sobreventa (28) sugiere reversión",
                "MACD cruzó alcista hace 2 períodos",
                "ADX (35) confirma tendencia fuerte"
            ],
            "timeframe_outlook": "4-12h",
            "risk_level": "MEDIUM"
        }
    }
    
    symbol = "BTC/USD"
    
    print(f"📱 Enviando mensaje de prueba para {symbol}...")
    print(f"🕐 Timestamp: {datetime.now()}")
    
    try:
        # Intentar enviar la alerta
        result = send_whatsapp_alert(mock_llm_result, symbol)
        
        print("\n📋 RESULTADO:")
        print("-" * 30)
        
        if result.get("success"):
            print("✅ ÉXITO: Mensaje enviado correctamente")
            print(f"📞 Teléfono: {result.get('phone', 'N/A')}")
            print(f"📄 Mensaje enviado:")
            print("-" * 20)
            print(result.get("message_sent", "N/A"))
            print("-" * 20)
        else:
            print("❌ ERROR: No se pudo enviar el mensaje")
            print(f"🔍 Error: {result.get('error', 'Desconocido')}")
            
            if "CALLMEBOT" in str(result.get('error', '')):
                print("\n💡 SOLUCIÓN:")
                print("1. Configura CALLMEBOT_PHONE en tu .env")
                print("2. Configura CALLMEBOT_APIKEY en tu .env")
                print("3. Verifica que el número esté registrado en CallMeBot")
        
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ EXCEPCIÓN: {e}")
        return False

def test_message_format_only():
    """Solo prueba el formato del mensaje sin enviar"""
    
    print("\n🎨 PREVIEW DEL FORMATO (SIN ENVIAR)")
    print("="*50)
    
    # Mismos datos simulados
    mock_llm_result = {
        "analysis": {
            "action": "SHORT",
            "confidence": 75,
            "entry_price": 59200,
            "stop_loss": 60500,
            "take_profit": 56800,
            "risk_reward_ratio": 1.8,
            "key_factors": [
                "RSI sobrecomprado (78) en territorio peligroso",
                "MACD mostrando divergencia bajista",
                "Precio rechazado en resistencia clave"
            ],
            "timeframe_outlook": "6-12h",
            "risk_level": "HIGH"
        }
    }
    
    try:
        from service.whatsapp_notifier import WhatsAppNotifier
        notifier = WhatsAppNotifier()
        message = notifier.format_trading_alert(mock_llm_result, "ETH/USD")
        
        print(message)
        print(f"\n📏 Longitud: {len(message)} caracteres")
        
    except Exception as e:
        print(f"Error en formato: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE WHATSAPP")
    print("="*60)
    
    # Primero mostrar formato
    test_message_format_only()
    
    print("\n" + "="*60)
    
    # Luego intentar envío real
    success = test_whatsapp_send()
    
    print("\n" + "="*60)
    print(f"🏁 RESULTADO FINAL: {'✅ ÉXITO' if success else '❌ FALLO'}")
    
    if not success:
        print("\n💭 NOTAS:")
        print("- Si no tienes credenciales configuradas, es normal que falle")
        print("- El formato del mensaje se muestra arriba")
        print("- Configura CALLMEBOT_PHONE y CALLMEBOT_APIKEY para envío real")
