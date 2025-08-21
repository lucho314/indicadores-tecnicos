import json
from typing import Dict, Any
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY

class LLMAnalyzer:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no configurada en las variables de entorno")
        
        # Crear cliente OpenAI con parámetros mínimos para evitar conflictos
        try:
            self.client = OpenAI(
                api_key=OPENAI_API_KEY,
                timeout=30.0,
                max_retries=2
            )
        except TypeError as e:
            if "proxies" in str(e):
                # Fallback si hay problema con proxies
                import os
                # Limpiar variables de entorno relacionadas con proxy
                proxy_vars = [k for k in os.environ.keys() if 'proxy' in k.lower()]
                for var in proxy_vars:
                    del os.environ[var]
                
                # Intentar nuevamente con configuración mínima
                self.client = OpenAI(api_key=OPENAI_API_KEY)
            else:
                raise e
        
        self.model = "gpt-4o"  # Modelo más avanzado para análisis técnico
    
    def _build_prompt(self, llm_context: Dict[str, Any]) -> str:
        """Construye el prompt profesional para análisis técnico"""
        
        latest = llm_context.get("latest", {})
        summary_30 = llm_context.get("summary_30", {})
        summary_60 = llm_context.get("summary_60", {})
        recent_points = llm_context.get("recent_points", [])
        events = summary_30.get("events", [])
        
        # Información de posición actual
        current_position = llm_context.get("current_position")
        has_position = llm_context.get("has_position", False)
        bybit_symbol = llm_context.get("bybit_symbol", "N/A")
        
        # Construir sección de posición actual
        position_section = ""
        if has_position and current_position:
            def safe_float(value, default=0):
                try:
                    return float(value) if value != '' and value is not None else default
                except (ValueError, TypeError):
                    return default
            
            position_side = current_position.get('side', 'N/A')
            position_size = safe_float(current_position.get('size', 0))
            avg_price = safe_float(current_position.get('avgPrice', 0))
            mark_price = safe_float(current_position.get('markPrice', 0))
            unrealised_pnl = safe_float(current_position.get('unrealisedPnl', 0))
            leverage = current_position.get('leverage', '1')
            
            pnl_status = "GANANDO" if unrealised_pnl > 0 else "PERDIENDO" if unrealised_pnl < 0 else "NEUTRO"
            
            position_section = f"""
## POSICIÓN ACTIVA EN BYBIT:
- **Símbolo**: {bybit_symbol}
- **Lado**: {position_side} ({"LARGO" if position_side == "Buy" else "CORTO" if position_side == "Sell" else "N/A"})
- **Tamaño**: {position_size}
- **Precio Promedio**: ${avg_price:,.2f}
- **Precio Marca**: ${mark_price:,.2f}
- **PnL No Realizado**: ${unrealised_pnl:,.2f} ({pnl_status})
- **Apalancamiento**: {leverage}x
- **Diferencia vs Marca**: {((mark_price - avg_price) / avg_price * 100):+.2f}% {"📈" if mark_price > avg_price else "📉" if mark_price < avg_price else "➡️"}

**GESTIÓN DE POSICIÓN REQUERIDA**: Dado que tienes una posición activa, tu análisis debe incluir:
1. ¿Mantener la posición actual?
2. ¿Cerrar parcial o totalmente?
3. ¿Mover el stop loss?
4. ¿Añadir más volumen (DCA)?
5. ¿Tomar ganancias parciales?
"""
        else:
            position_section = """
## ESTADO DE POSICIÓN:
- **Sin posiciones activas** - Análisis para nueva entrada
"""
        
        prompt = f"""
# ANÁLISIS TÉCNICO PROFESIONAL - TRADING APALANCADO 3X

**CONTEXTO OPERATIVO:**
- Símbolo: {llm_context.get('symbol', 'N/A')}
- Timeframe: {llm_context.get('tf', '4h')} (Análisis de horizonte medio)
- Apalancamiento: 3X (Gestión de riesgo crítica)
- Modalidad: LONG o SHORT disponibles
- Timestamp: {llm_context.get('now', 'N/A')}

{position_section}

## DATOS TÉCNICOS ACTUALES:
- **RSI**: {latest.get('rsi', 'N/A')} (Momentum)
- **MACD**: {latest.get('macd', 'N/A')} / Signal: {latest.get('macd_signal', 'N/A')} 
- **MACD Histogram**: {latest.get('macd_hist', 'N/A')} (Divergencia)
- **SMA**: {latest.get('sma', 'N/A')} (Precio actual vs tendencia)
- **ADX**: {latest.get('adx', 'N/A')} (Fuerza de tendencia)
- **Bollinger Bands**: Upper: {latest.get('bb_u', 'N/A')} | Middle: {latest.get('bb_m', 'N/A')} | Lower: {latest.get('bb_l', 'N/A')}
- **Precio Actual**: ${latest.get('close_price', 'N/A')}

## CONTEXTO HISTÓRICO (30h):
- RSI Range: {summary_30.get('rsi_min', 'N/A')}-{summary_30.get('rsi_max', 'N/A')} (Promedio: {summary_30.get('rsi_mean', 'N/A')})
- MACD Hist Promedio: {summary_30.get('macd_hist_mean', 'N/A')}
- Volatilidad BB: {summary_30.get('bb_bw_mean', 'N/A')}
- Distancia vs SMA: {summary_30.get('dist_sma_mean', 'N/A')}

## EVENTOS DETECTADOS:
{', '.join(events) if events else 'No hay eventos significativos detectados'}

## PUNTOS HISTÓRICOS RECIENTES:
{len(recent_points)} snapshots disponibles para análisis de momentum.

---

**INSTRUCCIONES DE ANÁLISIS:**

Eres un trader profesional experimentado con 10+ años en mercados cripto. {'Tu objetivo es gestionar la posición actual de manera óptima.' if has_position else 'Tu objetivo es identificar oportunidades de entrada con alto potencial risk/reward'} en timeframe 4H.

**ANALIZA:**
1. **Momentum**: ¿El RSI sugiere sobreventa (<30) o sobrecompra (>70)? ¿Hay divergencias?
2. **Tendencia**: ¿El MACD está cruzando? ¿El ADX muestra fuerza trending (>25)?
3. **Precio vs Media**: ¿Estamos cerca del SMA? ¿Rompiendo resistencia/soporte?
4. **Volatilidad**: ¿Las Bollinger Bands se están expandiendo/contrayendo?
5. **Contexto**: ¿Los eventos históricos apoyan la decisión?
{'6. **Gestión de Posición**: ¿La posición actual está en territorio favorable? ¿Necesita ajustes?' if has_position else ''}

**DECISIÓN REQUERIDA:**
{'- **ACCIÓN**: HOLD (mantener), CLOSE (cerrar), ADD (añadir), MOVE_SL (mover stop), TAKE_PROFIT (tomar ganancias)' if has_position else '- **ACCIÓN**: LONG, SHORT, o WAIT'}
- **CONFIANZA**: Alta (>80%), Media (50-80%), Baja (<50%)
{'- **JUSTIFICACIÓN**: Para gestión de posición existente' if has_position else '- **ENTRADA**: Precio específico sugerido'}
{'- **NUEVO_SL**: Nuevo nivel de stop loss si aplica' if has_position else '- **STOP LOSS**: Nivel de riesgo (máximo 2% con apalancamiento 3X)'}
{'- **NUEVO_TP**: Nuevo nivel de take profit si aplica' if has_position else '- **TAKE PROFIT**: Target realista para 4-12 horas'}
- **RAZÓN**: Argumentación técnica convincente y profesional

**PERFIL DE RIESGO**: {'Conservador para gestión de posición existente, proteger capital.' if has_position else 'Agresivo pero calculado. Toma posiciones cuando la probabilidad sea favorable, pero mantén gestión de riesgo estricta.'}

**RESPONDE EN FORMATO JSON CONCISO:**
```json
{{
  "action": "{'HOLD|CLOSE|ADD|MOVE_SL|TAKE_PROFIT' if has_position else 'LONG|SHORT|WAIT'}",
  "confidence": 85,
  {'  "justification": "Mantener posición, mercado favorable",' if has_position else '  "entry_price": 58500,'}
  {'  "new_stop_loss": 57200,' if has_position else '  "stop_loss": 57200,'}
  {'  "new_take_profit": 61200,' if has_position else '  "take_profit": 61200,'}
  "risk_reward_ratio": 2.3,
  "key_factors": ["Factor técnico 1", "Factor técnico 2", "Factor técnico 3"],
  "timeframe_outlook": "4-12h",
  "risk_level": "MEDIUM"{',' if has_position else ''}
  {'  "position_status": "FAVORABLE|NEUTRAL|UNFAVORABLE"' if has_position else ''}
}}
```

**INSTRUCCIONES ESPECÍFICAS:**
- Máximo 3 factores clave, cada uno en 1 línea
- Sin explicaciones largas, solo datos concisos
- Precios redondeados a enteros
- Confianza en porcentaje entero
{'- Considera el PnL actual y precio promedio en tus decisiones' if has_position else ''}
- Este mensaje se enviará por WhatsApp como alerta

**SÉ DECISIVO Y CONCISO.**
        """
        
        return prompt.strip()
    
    def analyze(self, llm_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza el contexto técnico y devuelve recomendación de trading
        
        Args:
            llm_context: Contexto completo con datos históricos y actuales
        
        Returns:
            Dict con la recomendación del LLM y metadatos
        """
        try:
            prompt = self._build_prompt(llm_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un trader profesional experto en análisis técnico y gestión de riesgo. Responde siempre en formato JSON válido."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Algo de creatividad pero mantener consistencia
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Extraer y parsear la respuesta JSON
            content = response.choices[0].message.content
            if not content:
                return {
                    "llm_called": True,
                    "error": "Empty response from OpenAI",
                    "timestamp": datetime.now().isoformat()
                }
                
            llm_analysis = json.loads(content)
            
            # Agregar metadatos
            return {
                "llm_called": True,
                "model_used": self.model,
                "timestamp": datetime.now().isoformat(),
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "analysis": llm_analysis,
                "context_points": len(llm_context.get("recent_points", [])),
                "raw_response": content
            }
            
        except json.JSONDecodeError as e:
            return {
                "llm_called": True,
                "error": f"Error parsing JSON response: {e}",
                "raw_response": content if 'content' in locals() else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "llm_called": True,
                "error": f"Error calling OpenAI API: {e}",
                "timestamp": datetime.now().isoformat()
            }

def llamar_llm(llm_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de interfaz para mantener compatibilidad con main.py
    
    Args:
        llm_context: Contexto completo con datos históricos y actuales
    
    Returns:
        Dict con la respuesta del LLM y metadatos
    """
    try:
        analyzer = LLMAnalyzer()
        return analyzer.analyze(llm_context)
    except Exception as e:
        return {
            "llm_called": False,
            "error": f"Error inicializando LLM: {e}",
            "timestamp": datetime.now().isoformat()
        }
