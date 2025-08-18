import sys
sys.path.append('.')

def format_trading_alert_preview():
    """Preview del formato sin dependencias de configuración"""
    
    # Simulación de datos del LLM
    analysis = {
        "action": "LONG",
        "confidence": 78,
        "entry_price": 58500,
        "stop_loss": 56930,
        "take_profit": 61000,
        "risk_reward_ratio": 1.85,
        "key_factors": [
            "RSI en sobreventa sugiriendo reversión alcista",
            "MACD cruce alcista reciente", 
            "ADX muestra fuerte tendencia"
        ],
        "timeframe_outlook": "4-12h",
        "risk_level": "MEDIUM"
    }
    
    # Emoji según la acción
    action_emoji = {
        "LONG": "🟢",
        "SHORT": "🔴", 
        "WAIT": "⏸️"
    }
    
    action = analysis.get("action", "WAIT")
    emoji = action_emoji.get(action, "⚪")
    symbol = "BTC/USD"
    
    # Formatear factores
    factors = analysis.get('key_factors', [])
    formatted_factors = []
    for factor in factors[:3]:  # Máximo 3 factores
        formatted_factors.append(f"• {factor}")
    factors_text = "\n".join(formatted_factors) if formatted_factors else "• No especificados"
    
    message = f"""🚨 ALERTA TRADING {emoji}

📊 {symbol}
Acción: {action}
Confianza: {analysis.get('confidence', 0)}%
Precio Entrada: ${analysis.get('entry_price', 'N/A')}
Stop Loss: ${analysis.get('stop_loss', 'N/A')}
Take Profit: ${analysis.get('take_profit', 'N/A')}
R/R Ratio: {analysis.get('risk_reward_ratio', 'N/A')}

🔑 Factores Clave:
{factors_text}

⚡ Horizonte: {analysis.get('timeframe_outlook', '4-12h')}
🎯 Riesgo: {analysis.get('risk_level', 'MEDIUM')}"""

    print("📱 PREVIEW DEL MENSAJE WHATSAPP:")
    print("="*50)
    print(message)
    print("="*50)
    print(f"Longitud: {len(message)} caracteres")

if __name__ == "__main__":
    format_trading_alert_preview()
