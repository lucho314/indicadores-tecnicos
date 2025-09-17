"""
Script para probar el envío de mensajes por Telegram
"""
import sys
import os
import json
from datetime import datetime

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service.telegram import TelegramService
from config import TELEGRAM_CHAT_ID

def test_simple_message():
    """Prueba el envío de un mensaje simple por Telegram"""
    try:
        # Inicializar el servicio de Telegram
        telegram = TelegramService()
        
        # Mensaje simple
        message = f"🧪 Prueba de mensaje desde el sistema de trading - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Enviar mensaje
        print(f"Enviando mensaje a chat_id: {TELEGRAM_CHAT_ID}")
        result = telegram.send_message(TELEGRAM_CHAT_ID, message)
        
        # Mostrar resultado
        print("✅ Mensaje enviado exitosamente")
        print(json.dumps(result, indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Error enviando mensaje: {e}")
        return False

def test_trading_alert():
    """Prueba el envío de una alerta de trading por Telegram"""
    try:
        # Inicializar el servicio de Telegram
        telegram = TelegramService()
        
        # Simular un análisis de trading
        mock_analysis = {
            "analysis": {
                "action": "LONG",
                "confidence": 85,
                "entry_price": 65432.50,
                "stop_loss": 64500.00,
                "take_profit": 67500.00,
                "risk_reward_ratio": 2.1,
                "key_factors": [
                    "RSI saliendo de zona de sobreventa",
                    "Cruce de medias móviles",
                    "Soporte fuerte en $64,500"
                ],
                "timeframe_outlook": "4-8h",
                "risk_level": "MEDIUM"
            }
        }
        
        # Formatear mensaje de alerta
        message = f"""🚨 ALERTA TRADING 🟢

📊 BTCUSDT
Acción: LONG
Confianza: 85%
Precio Entrada: $65432.50
Stop Loss: $64500.00
Take Profit: $67500.00
R/R Ratio: 2.1

🔑 Factores Clave:
• RSI saliendo de zona de sobreventa
• Cruce de medias móviles
• Soporte fuerte en $64,500

⚡ Horizonte: 4-8h
🎯 Riesgo: MEDIUM"""
        
        # Enviar mensaje
        print(f"Enviando alerta de trading a chat_id: {TELEGRAM_CHAT_ID}")
        result = telegram.send_message(TELEGRAM_CHAT_ID, message)
        
        # Mostrar resultado
        print("✅ Alerta de trading enviada exitosamente")
        print(json.dumps(result, indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Error enviando alerta de trading: {e}")
        return False

def test_using_whatsapp_formatter():
    """Prueba el envío de una alerta usando el formateador de WhatsApp"""
    try:
        from service.whatsapp_notifier import WhatsAppNotifier
        
        # Inicializar servicios
        telegram = TelegramService()
        whatsapp_formatter = WhatsAppNotifier()
        
        # Simular un análisis de trading
        mock_analysis = {
            "analysis": {
                "action": "SHORT",
                "confidence": 78,
                "entry_price": 65432.50,
                "stop_loss": 66500.00,
                "take_profit": 63500.00,
                "risk_reward_ratio": 1.8,
                "key_factors": [
                    "RSI en zona de sobrecompra",
                    "Divergencia bajista en MACD",
                    "Resistencia fuerte en $66,500"
                ],
                "timeframe_outlook": "4-12h",
                "risk_level": "HIGH"
            }
        }
        
        # Formatear mensaje usando el formateador de WhatsApp
        message = whatsapp_formatter.format_trading_alert(mock_analysis, "BTCUSDT")
        
        # Enviar mensaje
        print(f"Enviando alerta formateada a chat_id: {TELEGRAM_CHAT_ID}")
        result = telegram.send_message(TELEGRAM_CHAT_ID, message)
        
        # Mostrar resultado
        print("✅ Alerta formateada enviada exitosamente")
        print(json.dumps(result, indent=2))
        
        return True
    except Exception as e:
        print(f"❌ Error enviando alerta formateada: {e}")
        return False

if __name__ == "__main__":
    print("=== PRUEBA DE TELEGRAM ===")
    
    # Verificar que TELEGRAM_CHAT_ID esté configurado
    if not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_CHAT_ID no está configurado en el archivo .env")
        print("Por favor, configura la variable TELEGRAM_CHAT_ID en el archivo .env")
        sys.exit(1)
    
    # Ejecutar pruebas
    print("\n1. Prueba de mensaje simple:")
    test_simple_message()
    
    print("\n2. Prueba de alerta de trading:")
    test_trading_alert()
    
    print("\n3. Prueba usando formateador de WhatsApp:")
    test_using_whatsapp_formatter()
    
    print("\n=== PRUEBAS COMPLETADAS ===")