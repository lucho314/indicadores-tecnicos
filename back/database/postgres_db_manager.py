import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class PostgresIndicadorDB:
    def __init__(self, database_url: str = None):
        """
        Inicializar conexión a PostgreSQL
        database_url formato: postgresql://user:password@host:port/database
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'postgresql://indicadores_user:indicadores_pass123@localhost:5432/indicadores_db'
        )
        self.test_connection()
    
    def test_connection(self):
        """Probar la conexión a la base de datos"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    logger.info("✅ Conexión a PostgreSQL exitosa")
        except Exception as e:
            logger.error(f"❌ Error conectando a PostgreSQL: {e}")
            raise
    
    def get_connection(self):
        """Obtener conexión a la base de datos"""
        return psycopg2.connect(self.database_url)
    
    def save_indicators(self, data: Dict[str, Any], signal: bool = False) -> bool:
        """Guardar indicadores en la base de datos"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Preparar los datos
                    symbol = data.get('symbol', 'N/A')
                    interval_tf = data.get('interval', '4h')
                    timestamp = datetime.fromisoformat(data['timestamp'].replace('T', ' ').replace('Z', ''))
                    
                    # Los datos vienen directamente en el diccionario principal, no en 'indicators'
                    # Verificar estructura real de datos
                    print(f"DEBUG: Estructura de datos recibida: {list(data.keys())}")
                    print(f"DEBUG: close_price value: {data.get('close_price', 'NO_FOUND')}")
                    print(f"DEBUG: Muestra de datos: {dict(list(data.items())[:5])}")
                    print(f"DEBUG: Signal value: {signal}")
                    
                    # Usar close_price en lugar de price
                    price = float(data.get('close_price', data.get('price', 0)))
                    rsi = float(data.get('rsi', 0))
                    sma = float(data.get('sma', 0))
                    adx = float(data.get('adx', 0))
                    macd = float(data.get('macd', 0))
                    macd_signal = float(data.get('macd_signal', 0))
                    macd_hist = float(data.get('macd_hist', 0))
                    
                    # Bollinger Bands (si están disponibles)
                    bb_upper = float(data.get('bb_upper', 0))
                    bb_middle = float(data.get('bb_middle', 0))
                    bb_lower = float(data.get('bb_lower', 0))
                    
                    print(f"DEBUG: Price={price}, RSI={rsi}, MACD_Hist={macd_hist}, SMA={sma}")
                    
                    # Insertar en la base de datos
                    insert_query = """
                        INSERT INTO indicadores (
                            timestamp, symbol, interval_tf, price, rsi, sma, adx,
                            macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, signal, raw_data
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """
                    
                    cur.execute(insert_query, (
                        timestamp, symbol, interval_tf, price, rsi, sma, adx,
                        macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, signal,
                        json.dumps(data)
                    ))
                    
                    conn.commit()
                    logger.info(f"✅ Datos guardados: {symbol} - RSI: {rsi} - Signal: {signal}")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Error guardando en BD: {e}")
            return False
    
    def get_recent_indicators(self, symbol: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener indicadores recientes"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if symbol:
                        query = """
                            SELECT * FROM indicadores 
                            WHERE symbol = %s 
                            ORDER BY timestamp DESC 
                            LIMIT %s
                        """
                        cur.execute(query, (symbol, limit))
                    else:
                        query = """
                            SELECT * FROM indicadores 
                            ORDER BY timestamp DESC 
                            LIMIT %s
                        """
                        cur.execute(query, (limit,))
                    
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos: {e}")
            return []
    
    def build_context_for_llm(self, symbol: str, current_data: Dict[str, Any]) -> str:
        """Construir contexto histórico para el LLM"""
        try:
            recent_data = self.get_recent_indicators(symbol, 10)
            
            if not recent_data:
                return "No hay datos históricos disponibles."
            
            context_lines = [
                f"📊 CONTEXTO HISTÓRICO RECIENTE - {symbol}:",
                f"Datos de los últimos {len(recent_data)} registros:",
                ""
            ]
            
            for i, record in enumerate(recent_data[:5], 1):
                timestamp = record['timestamp'].strftime('%Y-%m-%d %H:%M')
                rsi = record['rsi']
                macd_hist = record['macd_hist']
                sma = record['sma']
                
                context_lines.append(
                    f"{i}. {timestamp} - RSI: {rsi:.2f}, MACD_Hist: {macd_hist:.2f}, SMA: {sma:.2f}"
                )
            
            # Estadísticas
            rsi_values = [r['rsi'] for r in recent_data if r['rsi']]
            macd_values = [r['macd_hist'] for r in recent_data if r['macd_hist']]
            
            if rsi_values:
                rsi_avg = sum(rsi_values) / len(rsi_values)
                rsi_min = min(rsi_values)
                rsi_max = max(rsi_values)
                
                context_lines.extend([
                    "",
                    f"📈 ESTADÍSTICAS RSI (últimos {len(rsi_values)} puntos):",
                    f"   Promedio: {rsi_avg:.2f}, Mín: {rsi_min:.2f}, Máx: {rsi_max:.2f}"
                ])
            
            if macd_values:
                macd_avg = sum(macd_values) / len(macd_values)
                positive_macd = sum(1 for v in macd_values if v > 0)
                
                context_lines.extend([
                    f"📊 MACD Histogram promedio: {macd_avg:.2f}",
                    f"   Valores positivos: {positive_macd}/{len(macd_values)} ({100*positive_macd/len(macd_values):.1f}%)"
                ])
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f"❌ Error construyendo contexto: {e}")
            return "Error obteniendo contexto histórico."
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Limpiar datos antiguos"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Limpiar indicadores antiguos
                    cur.execute(
                        "DELETE FROM indicadores WHERE timestamp < %s",
                        (cutoff_date,)
                    )
                    deleted_indicators = cur.rowcount
                    
                    # Limpiar logs antiguos
                    cur.execute(
                        "DELETE FROM execution_logs WHERE timestamp < %s",
                        (cutoff_date,)
                    )
                    deleted_logs = cur.rowcount
                    
                    conn.commit()
                    
                    logger.info(f"🧹 Limpieza completada: {deleted_indicators} indicadores, {deleted_logs} logs eliminados")
                    
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
    
    def log_execution(self, symbol: str, status: str, message: str, execution_time: float = None, error_details: str = None):
        """Registrar la ejecución en logs"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO execution_logs (symbol, status, message, execution_time_seconds, error_details)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (symbol, status, message, execution_time, error_details))
                    conn.commit()
                    
        except Exception as e:
            logger.error(f"❌ Error registrando log: {e}")
    
    def get_execution_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Obtener estadísticas de ejecución"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Estadísticas generales
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_executions,
                            COUNT(*) FILTER (WHERE status = 'success') as successful,
                            COUNT(*) FILTER (WHERE status = 'error') as errors,
                            AVG(execution_time_seconds) as avg_execution_time
                        FROM execution_logs 
                        WHERE timestamp > %s
                    """, (cutoff_time,))
                    
                    stats = dict(cur.fetchone())
                    
                    # Últimas ejecuciones
                    cur.execute("""
                        SELECT symbol, status, message, timestamp 
                        FROM execution_logs 
                        WHERE timestamp > %s 
                        ORDER BY timestamp DESC 
                        LIMIT 10
                    """, (cutoff_time,))
                    
                    stats['recent_executions'] = [dict(row) for row in cur.fetchall()]
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {}
