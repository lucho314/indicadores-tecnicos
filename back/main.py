import sys
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
from service.indicadores_tecnicos import obtener_indicadores
from service.llm_analyzer import llamar_llm
from service.whatsapp_notifier import send_whatsapp_alert
from database.postgres_db_manager import PostgresIndicadorDB

def main(symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Función principal del análisis de indicadores
    
    Args:
        symbol: Símbolo de la criptomoneda (opcional)
    
    Returns:
        Dict con el resultado del análisis
    """
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] Iniciando análisis de indicadores...")
    
    # Inicializar base de datos PostgreSQL
    db = PostgresIndicadorDB()
    
    if symbol:
        print(f"[{timestamp}] Símbolo recibido por parámetro: {symbol}")
    
    # Obtener indicadores
    print(f"[{timestamp}] Obteniendo indicadores...")
    data = obtener_indicadores(symbol) if symbol else obtener_indicadores()
    
    result = {
        "timestamp": timestamp,
        "symbol": data.get("symbol", "N/A"),
        "interval": data.get("interval", "N/A"),
        "conditions_met": False,
        "llm_called": False,
        "errors": None
    }
    
    # Verificar si hay errores
    if "errors" in data:
        error_msg = f"Error al obtener indicadores: {data['errors']}"
        print(f"[{timestamp}] {error_msg}")
        result["errors"] = data["errors"]
        return result
    
    # Obtener valores con manejo de None
    rsi = data.get("rsi")
    macd_hist = data.get("macd_hist")
    
    # Agregar timestamp y guardar en BD (necesitaremos el precio de cierre también)
    data["timestamp"] = timestamp
    data["close_price"] = data.get("close_price", 0)  # Asegurarse de tener un precio de cierre
    
    # Inicialmente la señal es False
    signal_active = False
    
    # Guardar en base de datos (sin señal inicialmente)
    if db.save_indicators(data, signal=signal_active):
        print(f"[{timestamp}] Datos guardados en BD exitosamente")
    else:
        print(f"[{timestamp}] ⚠️ Error guardando en BD")
    
    result.update({
        "rsi": rsi,
        "macd_hist": macd_hist,
        "sma": data.get("sma"),
        "adx": data.get("adx"),
        "macd": data.get("macd"),
        "macd_signal": data.get("macd_signal")
    })
    
    # Verificar condiciones manejando valores None
    rsi_condition = rsi is not None and rsi < 30
    macd_condition = macd_hist is not None and macd_hist > 0
    
    if rsi_condition or macd_condition:
        print(f"[{timestamp}] CONDICIONES CUMPLIDAS: RSI < 30 o MACD_Hist > 0")
        print(f"[{timestamp}] RSI: {rsi}, MACD_Hist: {macd_hist}")
        
        # Construir contexto para LLM
        historical_context = db.build_context_for_llm(data.get("symbol", "N/A"), data)
        
        # Crear contexto estructurado para el LLM
        llm_context = {
            "latest": data,
            "historical_summary": historical_context,
            "symbol": data.get("symbol", "N/A"),
            "timestamp": timestamp
        }
        
        # Llamar a LLM con contexto completo
        llm_result = llamar_llm(llm_context)
        
        result.update({
            "conditions_met": True,
            "llm_called": True,
            "llm_result": llm_result
        })
        
        if llm_result.get("llm_called") and not llm_result.get("error"):
            print(f"[{timestamp}] LLM ejecutado exitosamente")
            
            # Verificar si hay una señal activa (acción != 'WAIT')
            analysis = llm_result.get("analysis", {})
            action = analysis.get("action", "WAIT")
            
            if action and action != "WAIT":
                signal_active = True
                print(f"[{timestamp}] ✅ SEÑAL ACTIVA: {action}")
                
                # Actualizar la base de datos con la señal activa
                try:
                    with db.get_connection() as conn:
                        with conn.cursor() as cur:
                            # Buscar el registro más reciente para este símbolo y actualizarlo
                            cur.execute("""
                                UPDATE indicadores 
                                SET signal = %s 
                                WHERE symbol = %s AND timestamp = %s
                            """, (True, data.get("symbol", "N/A"), datetime.fromisoformat(timestamp.replace('T', ' ').replace('Z', ''))))
                            conn.commit()
                            print(f"[{timestamp}] ✅ Señal actualizada en BD")
                except Exception as e:
                    print(f"[{timestamp}] ⚠️ Error actualizando señal en BD: {e}")
            else:
                print(f"[{timestamp}] No hay señal activa (acción: {action})")
            
            # Enviar alerta por WhatsApp
            print(f"[{timestamp}] Enviando alerta por WhatsApp...")
            whatsapp_result = send_whatsapp_alert(llm_result, data.get("symbol", "N/A"))
            
            result["whatsapp_result"] = whatsapp_result
            result["signal_active"] = signal_active
            result["action"] = action
            
            if whatsapp_result.get("success"):
                print(f"[{timestamp}] ALERTA WhatsApp enviada exitosamente")
            else:
                print(f"[{timestamp}] ERROR enviando WhatsApp: {whatsapp_result.get('error', 'Unknown')}")
        else:
            print(f"[{timestamp}] ERROR en LLM: {llm_result.get('error', 'Unknown')}")
    else:
        print(f"[{timestamp}] Condiciones no cumplidas. No se llama a LLM.")
        print(f"[{timestamp}] RSI: {rsi}, MACD_Hist: {macd_hist}")
    
    # Limpiar datos antiguos ocasionalmente
    if timestamp.endswith("00:00"):  # Una vez por hora
        db.cleanup_old_data(30)
        print(f"[{timestamp}] Limpieza de datos antiguos completada")
    
    print(f"[{timestamp}] Análisis completado")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análisis de indicadores técnicos")
    parser.add_argument("--symbol", "-s", type=str, help="Símbolo de la criptomoneda (ej: BTC/USD)")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    
    args = parser.parse_args()
    
    result = main(args.symbol)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(f"\n{'='*50}")
        print("RESUMEN DEL ANÁLISIS")
        print(f"{'='*50}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Símbolo: {result['symbol']}")
        print(f"Condiciones cumplidas: {'SI' if result['conditions_met'] else 'NO'}")
        print(f"LLM llamado: {'SI' if result['llm_called'] else 'NO'}")
        if result['errors']:
            print(f"Errores: {result['errors']}")
