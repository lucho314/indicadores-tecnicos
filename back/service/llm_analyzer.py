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
        
        prompt = f"""
# ANÁLISIS TÉCNICO PROFESIONAL - TRADING APALANCADO 3X

**CONTEXTO OPERATIVO:**
- Símbolo: {llm_context.get('symbol', 'N/A')}
- Timeframe: {llm_context.get('tf', '4h')} (Análisis de horizonte medio)
- Apalancamiento: 3X (Gestión de riesgo crítica)
- Modalidad: LONG o SHORT disponibles
- Timestamp: {llm_context.get('now', 'N/A')}

## DATOS TÉCNICOS ACTUALES:
- **RSI**: {latest.get('rsi', 'N/A')} (Momentum)
- **MACD**: {latest.get('macd', 'N/A')} / Signal: {latest.get('macd_signal', 'N/A')} 
- **MACD Histogram**: {latest.get('macd_hist', 'N/A')} (Divergencia)
- **SMA**: {latest.get('sma', 'N/A')} (Precio actual vs tendencia)
- **ADX**: {latest.get('adx', 'N/A')} (Fuerza de tendencia)
- **Bollinger Bands**: Upper: {latest.get('bb_u', 'N/A')} | Middle: {latest.get('bb_m', 'N/A')} | Lower: {latest.get('bb_l', 'N/A')}

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

Eres un trader profesional experimentado con 10+ años en mercados cripto. Tu objetivo es identificar oportunidades de entrada con alto potencial risk/reward en timeframe 4H.

**ANALIZA:**
1. **Momentum**: ¿El RSI sugiere sobreventa (<30) o sobrecompra (>70)? ¿Hay divergencias?
2. **Tendencia**: ¿El MACD está cruzando? ¿El ADX muestra fuerza trending (>25)?
3. **Precio vs Media**: ¿Estamos cerca del SMA? ¿Rompiendo resistencia/soporte?
4. **Volatilidad**: ¿Las Bollinger Bands se están expandiendo/contrayendo?
5. **Contexto**: ¿Los eventos históricos apoyan una entrada ahora?

**DECISIÓN REQUERIDA:**
- **ACCIÓN**: LONG, SHORT, o WAIT
- **CONFIANZA**: Alta (>80%), Media (50-80%), Baja (<50%)
- **ENTRADA**: Precio específico sugerido
- **STOP LOSS**: Nivel de riesgo (máximo 2% con apalancamiento 3X)
- **TAKE PROFIT**: Target realista para 4-12 horas
- **RAZÓN**: Argumentación técnica convincente y profesional

**PERFIL DE RIESGO**: Agresivo pero calculado. Toma posiciones cuando la probabilidad sea favorable, pero mantén gestión de riesgo estricta.

**RESPONDE EN FORMATO JSON CONCISO:**
```json
{{
  "action": "LONG|SHORT|WAIT",
  "confidence": 85,
  "entry_price": 58500,
  "stop_loss": 57200,
  "take_profit": 61200,
  "risk_reward_ratio": 2.3,
  "key_factors": ["RSI en sobreventa sugiriendo reversión alcista", "MACD cruce alcista reciente", "ADX muestra fuerte tendencia"],
  "timeframe_outlook": "4-12h",
  "risk_level": "MEDIUM"
}}
```

**INSTRUCCIONES ESPECÍFICAS:**
- Máximo 3 factores clave, cada uno en 1 línea
- Sin explicaciones largas, solo datos concisos
- Precios redondeados a enteros
- Confianza en porcentaje entero
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
