import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
from database.postgres_db_manager import PostgresIndicadorDB

logger = logging.getLogger(__name__)

class KlinesService:
    """
    Servicio para obtener y gestionar datos de velas (klines) desde Bybit
    Maneja sincronización inicial y actualizaciones incrementales
    """
    
    def __init__(self, db_manager: PostgresIndicadorDB = None):
        self.base_url = "https://api.bybit.com/v5/market/kline"
        self.db_manager = db_manager or PostgresIndicadorDB()
        
    def fetch_klines_from_api(self, symbol: str = "BTCUSDT", interval: str = "240", 
                             limit: int = 1000, start_time: int = None, end_time: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene datos de velas desde la API de Bybit
        
        Args:
            symbol: Par de trading (ej: BTCUSDT)
            interval: Intervalo de tiempo (240=4h, 60=1h, 15=15m)
            limit: Número máximo de velas (max 1000)
            start_time: Timestamp de inicio en milisegundos
            end_time: Timestamp de fin en milisegundos
            
        Returns:
            Lista de diccionarios con datos de velas
        """
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if start_time:
                params["start"] = start_time
            if end_time:
                params["end"] = end_time
                
            logger.info(f"🔄 Obteniendo klines: {symbol} {interval} (limit={limit})")
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("retCode") != 0:
                raise Exception(f"Error de API Bybit: {data.get('retMsg')}")
                
            klines_raw = data.get("result", {}).get("list", [])
            
            # Convertir formato de Bybit a nuestro formato
            klines = []
            for kline in klines_raw:
                # Formato Bybit: [startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover]
                klines.append({
                    "symbol": symbol,
                    "interval_type": interval,
                    "open_time": int(kline[0]),
                    "close_time": int(kline[0]) + self._get_interval_ms(interval) - 1,
                    "open_price": float(kline[1]),
                    "high_price": float(kline[2]),
                    "low_price": float(kline[3]),
                    "close_price": float(kline[4]),
                    "volume": float(kline[5]),
                    "turnover": float(kline[6]) if len(kline) > 6 else 0.0
                })
                
            logger.info(f"✅ Obtenidas {len(klines)} velas de {symbol}")
            return klines
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo klines: {e}")
            raise
            
    def _get_interval_ms(self, interval: str) -> int:
        """
        Convierte intervalo a milisegundos
        """
        interval_map = {
            "1": 60 * 1000,           # 1 minuto
            "3": 3 * 60 * 1000,       # 3 minutos
            "5": 5 * 60 * 1000,       # 5 minutos
            "15": 15 * 60 * 1000,     # 15 minutos
            "30": 30 * 60 * 1000,     # 30 minutos
            "60": 60 * 60 * 1000,     # 1 hora
            "120": 2 * 60 * 60 * 1000, # 2 horas
            "240": 4 * 60 * 60 * 1000, # 4 horas
            "360": 6 * 60 * 60 * 1000, # 6 horas
            "720": 12 * 60 * 60 * 1000, # 12 horas
            "D": 24 * 60 * 60 * 1000,  # 1 día
            "W": 7 * 24 * 60 * 60 * 1000, # 1 semana
        }
        return interval_map.get(interval, 4 * 60 * 60 * 1000)  # default 4h
        
    def save_klines_to_db(self, klines: List[Dict[str, Any]]) -> int:
        """
        Guarda velas en la base de datos
        
        Returns:
            Número de velas guardadas
        """
        if not klines:
            return 0
            
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    saved_count = 0
                    
                    for kline in klines:
                        try:
                            insert_query = """
                                INSERT INTO klines (
                                    symbol, interval_type, open_time, close_time,
                                    open_price, high_price, low_price, close_price,
                                    volume, turnover
                                ) VALUES (
                                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                                )
                                ON CONFLICT (symbol, interval_type, open_time) 
                                DO UPDATE SET
                                    close_time = EXCLUDED.close_time,
                                    open_price = EXCLUDED.open_price,
                                    high_price = EXCLUDED.high_price,
                                    low_price = EXCLUDED.low_price,
                                    close_price = EXCLUDED.close_price,
                                    volume = EXCLUDED.volume,
                                    turnover = EXCLUDED.turnover,
                                    updated_at = CURRENT_TIMESTAMP
                            """
                            
                            cur.execute(insert_query, (
                                kline["symbol"],
                                kline["interval_type"],
                                kline["open_time"],
                                kline["close_time"],
                                kline["open_price"],
                                kline["high_price"],
                                kline["low_price"],
                                kline["close_price"],
                                kline["volume"],
                                kline["turnover"]
                            ))
                            saved_count += 1
                            
                        except psycopg2.IntegrityError:
                            # Vela duplicada, continuar
                            continue
                            
                    conn.commit()
                    logger.info(f"✅ Guardadas {saved_count} velas en BD")
                    return saved_count
                    
        except Exception as e:
            logger.error(f"❌ Error guardando velas: {e}")
            raise
            
    def get_latest_kline_time(self, symbol: str, interval: str) -> Optional[int]:
        """
        Obtiene el timestamp de la última vela guardada
        
        Returns:
            Timestamp en milisegundos o None si no hay datos
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT MAX(open_time) FROM klines WHERE symbol = %s AND interval_type = %s",
                        (symbol, interval)
                    )
                    result = cur.fetchone()
                    return result[0] if result and result[0] else None
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo última vela: {e}")
            return None
            
    def initial_sync(self, symbol: str = "BTCUSDT", interval: str = "240") -> int:
        """
        Sincronización inicial: obtiene las últimas 1000 velas
        
        Returns:
            Número de velas sincronizadas
        """
        logger.info(f"🔄 Iniciando sincronización inicial para {symbol} {interval}")
        
        klines = self.fetch_klines_from_api(symbol, interval, limit=1000)
        saved_count = self.save_klines_to_db(klines)
        
        logger.info(f"✅ Sincronización inicial completada: {saved_count} velas")
        return saved_count
        
    def incremental_sync(self, symbol: str = "BTCUSDT", interval: str = "240") -> int:
        """
        Sincronización incremental: obtiene solo velas nuevas
        
        Returns:
            Número de velas nuevas sincronizadas
        """
        logger.info(f"🔄 Iniciando sincronización incremental para {symbol} {interval}")
        
        # Obtener timestamp de la última vela
        latest_time = self.get_latest_kline_time(symbol, interval)
        
        if not latest_time:
            logger.warning("No hay datos previos, ejecutando sincronización inicial")
            return self.initial_sync(symbol, interval)
            
        # Obtener velas desde la última + 1 intervalo
        start_time = latest_time + self._get_interval_ms(interval)
        
        klines = self.fetch_klines_from_api(
            symbol, interval, 
            limit=500,  # Menos límite para actualizaciones
            start_time=start_time
        )
        
        saved_count = self.save_klines_to_db(klines)
        
        logger.info(f"✅ Sincronización incremental completada: {saved_count} velas nuevas")
        return saved_count
        
    def maintain_sliding_window(self, symbol: str = "BTCUSDT", interval: str = "240", 
                               keep_count: int = 1000) -> int:
        """
        Mantiene una ventana deslizante de las últimas N velas
        
        Args:
            keep_count: Número de velas a mantener
            
        Returns:
            Número de velas eliminadas
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Eliminar velas antiguas, manteniendo solo las últimas keep_count
                    delete_query = """
                        DELETE FROM klines 
                        WHERE symbol = %s AND interval_type = %s
                        AND open_time < (
                            SELECT open_time 
                            FROM klines 
                            WHERE symbol = %s AND interval_type = %s
                            ORDER BY open_time DESC 
                            LIMIT 1 OFFSET %s
                        )
                    """
                    
                    cur.execute(delete_query, (symbol, interval, symbol, interval, keep_count))
                    deleted_count = cur.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"🗑️ Eliminadas {deleted_count} velas antiguas (manteniendo {keep_count})")
                    
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"❌ Error manteniendo ventana deslizante: {e}")
            return 0
            
    def get_klines_for_calculation(self, symbol: str = "BTCUSDT", interval: str = "240", 
                                  limit: int = 200, exclude_current: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene velas para cálculo de indicadores
        
        Args:
            exclude_current: Si True, excluye la vela actual (en curso)
            
        Returns:
            Lista de velas ordenadas por tiempo (más antigua primero)
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    
                    if exclude_current:
                        # Excluir la última vela (puede estar en curso)
                        query = """
                            SELECT * FROM klines 
                            WHERE symbol = %s AND interval_type = %s
                            AND open_time < (
                                SELECT MAX(open_time) FROM klines 
                                WHERE symbol = %s AND interval_type = %s
                            )
                            ORDER BY open_time ASC 
                            LIMIT %s
                        """
                        cur.execute(query, (symbol, interval, symbol, interval, limit))
                    else:
                        query = """
                            SELECT * FROM klines 
                            WHERE symbol = %s AND interval_type = %s
                            ORDER BY open_time ASC 
                            LIMIT %s
                        """
                        cur.execute(query, (symbol, interval, limit))
                        
                    return [dict(row) for row in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo velas para cálculo: {e}")
            return []