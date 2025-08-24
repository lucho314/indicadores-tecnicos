import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

class IndicadorDB:
    def __init__(self, db_path: str = "indicadores.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos y crea las tablas necesarias"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS indicadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    interval_tf TEXT NOT NULL,
                    close_price REAL,
                    rsi REAL,
                    sma REAL,
                    adx REAL,
                    macd REAL,
                    macd_signal REAL,
                    macd_hist REAL,
                    bb_upper REAL,
                    bb_middle REAL,
                    bb_lower REAL,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    signal BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Índices para mejorar rendimiento
            conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON indicadores(symbol, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON indicadores(created_at)")
            
            conn.commit()
    
    def save_indicators(self, data: Dict[str, Any]) -> bool:
        """Guarda un snapshot de indicadores en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO indicadores (
                        timestamp, symbol, interval_tf, close_price, rsi, sma, adx,
                        macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get("timestamp"),
                    data.get("symbol"),
                    data.get("interval"),
                    data.get("close_price"),  # Necesitaremos agregarlo
                    data.get("rsi"),
                    data.get("sma"),
                    data.get("adx"),
                    data.get("macd"),
                    data.get("macd_signal"),
                    data.get("macd_hist"),
                    data.get("bb_upper"),
                    data.get("bb_middle"),
                    data.get("bb_lower"),
                    json.dumps(data)
                ))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error guardando indicadores: {e}")
            return False
    
    def get_recent_indicators(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtiene los últimos N indicadores para un símbolo"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM indicadores 
                WHERE symbol = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (symbol, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_summary_stats(self, symbol: str, hours: int = 30) -> Dict[str, Any]:
        """Calcula estadísticas resumidas para las últimas N horas"""
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    MIN(rsi) as rsi_min,
                    MAX(rsi) as rsi_max,
                    AVG(rsi) as rsi_mean,
                    AVG(macd_hist) as macd_hist_mean,
                    AVG((bb_upper - bb_lower) / bb_middle) as bb_bw_mean,
                    AVG(ABS(close_price - sma) / sma) as dist_sma_mean,
                    COUNT(*) as count
                FROM indicadores 
                WHERE symbol = ? AND created_at > ?
            """, (symbol, cutoff_time))
            
            result = cursor.fetchone()
            if result and result[6] > 0:  # count > 0
                return {
                    "rsi_min": round(result[0], 1) if result[0] else None,
                    "rsi_max": round(result[1], 1) if result[1] else None,
                    "rsi_mean": round(result[2], 1) if result[2] else None,
                    "macd_hist_mean": round(result[3], 3) if result[3] else None,
                    "bb_bw_mean": round(result[4], 3) if result[4] else None,
                    "dist_sma_mean": round(result[5], 3) if result[5] else None,
                    "events": self._detect_events(symbol, hours)
                }
            return {}
    
    def _detect_events(self, symbol: str, hours: int) -> List[str]:
        """Detecta eventos importantes en el período especificado"""
        events = []
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # MACD Cross Up/Down
            cursor = conn.execute("""
                SELECT macd_hist, created_at,
                       LAG(macd_hist) OVER (ORDER BY created_at) as prev_macd_hist
                FROM indicadores 
                WHERE symbol = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 10
            """, (symbol, cutoff_time))
            
            rows = cursor.fetchall()
            for i, (curr_hist, timestamp, prev_hist) in enumerate(rows):
                if prev_hist is not None and curr_hist is not None:
                    if prev_hist <= 0 and curr_hist > 0:
                        events.append(f"macd_cross_up@t-{i}")
                    elif prev_hist >= 0 and curr_hist < 0:
                        events.append(f"macd_cross_down@t-{i}")
            
            # RSI eventos
            cursor = conn.execute("""
                SELECT rsi, created_at,
                       LAG(rsi) OVER (ORDER BY created_at) as prev_rsi
                FROM indicadores 
                WHERE symbol = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT 10
            """, (symbol, cutoff_time))
            
            rows = cursor.fetchall()
            for i, (curr_rsi, timestamp, prev_rsi) in enumerate(rows):
                if prev_rsi is not None and curr_rsi is not None:
                    if prev_rsi <= 30 and curr_rsi > 30:
                        events.append(f"rsi_out_of_oversold@t-{i}")
                    elif prev_rsi >= 70 and curr_rsi < 70:
                        events.append(f"rsi_out_of_overbought@t-{i}")
        
        return events
    
    def cleanup_old_data(self, days: int = 30):
        """Limpia datos antiguos para mantener la base optimizada"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM indicadores WHERE created_at < ?", (cutoff_date,))
            conn.execute("VACUUM")  # Optimiza la base de datos
            conn.commit()
    
    def build_llm_context(self, symbol: str, latest_data: Dict[str, Any]) -> Dict[str, Any]:
        """Construye el contexto completo para enviar al LLM"""
        recent_points = self.get_recent_indicators(symbol, 12)
        
        # Convertir recent_points a formato compacto
        compact_points = []
        for point in recent_points[1:]:  # Excluir el más reciente (ya está en latest)
            compact_points.append({
                "t": point["timestamp"],
                "c": point["close_price"],
                "rsi": point["rsi"],
                "macd_h": point["macd_hist"],
                "sma": point["sma"]
            })
        
        return {
            "symbol": symbol,
            "tf": latest_data.get("interval", "N/A"),
            "now": datetime.now().isoformat(),
            "latest": {
                "close": latest_data.get("close_price"),
                "rsi": latest_data.get("rsi"),
                "macd": latest_data.get("macd"),
                "macd_signal": latest_data.get("macd_signal"),
                "macd_hist": latest_data.get("macd_hist"),
                "sma": latest_data.get("sma"),
                "sma200": latest_data.get("sma200"),
                "ema20": latest_data.get("ema20"),
                "ema200": latest_data.get("ema200"),
                "adx": latest_data.get("adx"),
                "atr14": latest_data.get("atr14"),
                "obv": latest_data.get("obv"),
                "volume": latest_data.get("volume"),
                "bb_u": latest_data.get("bb_upper"),
                "bb_m": latest_data.get("bb_middle"),
                "bb_l": latest_data.get("bb_lower")
            },
            "recent_points": compact_points,
            "summary_30": self.get_summary_stats(symbol, 30),
            "summary_60": self.get_summary_stats(symbol, 60)
        }
