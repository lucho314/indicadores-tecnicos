import requests
from typing import Dict, Any, Optional
from urllib.parse import quote
from config import CALLMEBOT_PHONE, CALLMEBOT_APIKEY
from service.telegram import TelegramService

class WhatsAppNotifier:
    def __init__(self):
        if not CALLMEBOT_PHONE or not CALLMEBOT_APIKEY:
            raise ValueError("CALLMEBOT_PHONE y CALLMEBOT_APIKEY deben estar configurados")
        
        self.phone = CALLMEBOT_PHONE
        self.apikey = CALLMEBOT_APIKEY
        self.base_url = "https://api.callmebot.com/whatsapp.php"
    
    def send_alert(self, message: str) -> Dict[str, Any]:
        """
        Envía alerta de trading por WhatsApp
        
        Args:
            message: Mensaje a enviar
        
        Returns:
            Dict con resultado del envío
        """
        try:
            # Codificar mensaje para URL
            encoded_message = quote(message)
            
            # Construir URL
            url = f"{self.base_url}?phone={self.phone}&text={encoded_message}&apikey={self.apikey}"
            
            # Enviar solicitud
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Alerta enviada exitosamente",
                    "phone": self.phone
                }
            else:
                return {
                    "success": False,
                    "error": f"Error HTTP {response.status_code}: {response.text}",
                    "phone": self.phone
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error enviando WhatsApp: {str(e)}",
                "phone": self.phone
            }
    
    def format_trading_alert(self, llm_analysis: Dict[str, Any], symbol: str) -> str:
        """
        Formatea la respuesta del LLM para WhatsApp
        
        Args:
            llm_analysis: Análisis del LLM
            symbol: Símbolo del activo
        
        Returns:
            Mensaje formateado para WhatsApp
        """
        analysis = llm_analysis.get("analysis", {})
        
        # Emoji según la acción
        action_emoji = {
            "LONG": "🟢",
            "SHORT": "🔴", 
            "WAIT": "⏸️"
        }
        
        action = analysis.get("action", "WAIT")
        emoji = action_emoji.get(action, "⚪")
        
        message = f"""🚨 ALERTA TRADING {emoji}

📊 {symbol}
Acción: {action}
Confianza: {analysis.get('confidence', 0)}%
Precio Entrada: ${analysis.get('entry_price', 'N/A')}
Stop Loss: ${analysis.get('stop_loss', 'N/A')}
Take Profit: ${analysis.get('take_profit', 'N/A')}
R/R Ratio: {analysis.get('risk_reward_ratio', 'N/A')}

🔑 Factores Clave:
{self._format_factors(analysis.get('key_factors', []))}

⚡ Horizonte: {analysis.get('timeframe_outlook', '4-12h')}
🎯 Riesgo: {analysis.get('risk_level', 'MEDIUM')}"""

        return message
    
    def _format_factors(self, factors: list) -> str:
        """Formatea la lista de factores para WhatsApp"""
        if not factors:
            return "• No especificados"
        
        formatted = []
        for i, factor in enumerate(factors[:3], 1):  # Máximo 3 factores
            formatted.append(f"• {factor}")
        
        return "\n".join(formatted)

def send_whatsapp_alert(llm_result: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    """
    Función de interfaz para enviar alertas de trading
    
    Args:
        llm_result: Resultado completo del análisis LLM
        symbol: Símbolo del activo
    
    Returns:
        Dict con resultado del envío
    """
    try:
        notifier = TelegramService()
        
        # Formatear mensaje (usando la misma función de formato)
        whatsapp_formatter = WhatsAppNotifier()
        message = whatsapp_formatter.format_trading_alert(llm_result, symbol)
        
        # Enviar alerta por Telegram (usando el chat_id de configuración)
        from config import TELEGRAM_CHAT_ID
        result = notifier.send_message(TELEGRAM_CHAT_ID, message)
        
        # Agregar información adicional
        result["message_sent"] = message
        result["symbol"] = symbol
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error en servicio WhatsApp: {str(e)}",
            "symbol": symbol
        }
