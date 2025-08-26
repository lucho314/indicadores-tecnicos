import logging
from typing import Dict, Any, Optional
from datetime import datetime
from service.klines_service import KlinesService
from service.technical_indicators import TechnicalIndicatorsCalculator
from database.postgres_db_manager import PostgresIndicadorDB

logger = logging.getLogger(__name__)

class IndicatorsEngine:
    """
    Motor principal para la reingeniería de indicadores técnicos
    Integra sincronización de datos de Bybit y cálculo de indicadores
    """
    
    def __init__(self, db_manager: PostgresIndicadorDB = None):
        self.db_manager = db_manager or PostgresIndicadorDB()
        self.klines_service = KlinesService(self.db_manager)
        self.indicators_calculator = TechnicalIndicatorsCalculator()
        
    def initialize_system(self, symbol: str = "BTCUSDT", interval: str = "240") -> bool:
        """
        Inicializa el sistema completo:
        1. Crea las tablas necesarias
        2. Ejecuta sincronización inicial
        3. Calcula indicadores iniciales
        
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            logger.info(f"🚀 Inicializando sistema de indicadores para {symbol} {interval}")
            
            # 1. Crear tablas (ejecutar migración)
            self._create_tables()
            
            # 2. Sincronización inicial
            logger.info("📥 Ejecutando sincronización inicial...")
            synced_count = self.klines_service.initial_sync(symbol, interval)
            
            if synced_count == 0:
                logger.error("❌ No se pudieron sincronizar datos iniciales")
                return False
                
            # 3. Calcular indicadores iniciales
            logger.info("📊 Calculando indicadores iniciales...")
            indicators = self.calculate_current_indicators(symbol, interval)
            
            if not indicators:
                logger.error("❌ No se pudieron calcular indicadores iniciales")
                return False
                
            logger.info(f"✅ Sistema inicializado exitosamente")
            logger.info(f"📈 Precio actual: ${indicators.get('close_price', 0):.2f}")
            logger.info(f"📊 RSI: {indicators.get('rsi14', 0):.2f}")
            logger.info(f"📈 EMA20: ${indicators.get('ema20', 0):.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            return False
            
    def _create_tables(self):
        """
        Ejecuta la migración para crear las tablas necesarias
        """
        try:
            # Leer y ejecutar el script de migración
            import os
            script_path = os.path.join(os.path.dirname(__file__), "..", "database", "create_klines_table.sql")
            
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                    
                with self.db_manager.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql_script)
                        conn.commit()
                        
                logger.info("✅ Tablas creadas exitosamente")
            else:
                logger.warning("⚠️ Script de migración no encontrado, asumiendo tablas existentes")
                
        except Exception as e:
            logger.error(f"❌ Error creando tablas: {e}")
            raise
            
    def update_data(self, symbol: str = "BTCUSDT", interval: str = "240") -> Dict[str, Any]:
        """
        Actualiza datos y calcula indicadores:
        1. Sincronización incremental
        2. Mantiene ventana deslizante
        3. Calcula nuevos indicadores
        
        Returns:
            Diccionario con indicadores actualizados
        """
        try:
            logger.info(f"🔄 Actualizando datos para {symbol} {interval}")
            
            # 1. Sincronización incremental
            new_klines = self.klines_service.incremental_sync(symbol, interval)
            logger.info(f"📥 Sincronizadas {new_klines} velas nuevas")
            
            # 2. Mantener ventana deslizante
            deleted_count = self.klines_service.maintain_sliding_window(symbol, interval, keep_count=1000)
            if deleted_count > 0:
                logger.info(f"🗑️ Eliminadas {deleted_count} velas antiguas")
                
            # 3. Calcular indicadores actualizados
            indicators = self.calculate_current_indicators(symbol, interval)
            
            if indicators:
                # 4. Guardar en la tabla de indicadores existente
                self._save_indicators_to_legacy_table(indicators)
                
                logger.info(f"✅ Datos actualizados exitosamente")
                logger.info(f"📈 Precio: ${indicators.get('close_price', 0):.2f}")
                logger.info(f"📊 RSI: {indicators.get('rsi14', 0):.2f}")
                
            return indicators or {}
            
        except Exception as e:
            logger.error(f"❌ Error actualizando datos: {e}")
            return {}
            
    def calculate_current_indicators(self, symbol: str = "BTCUSDT", interval: str = "240") -> Optional[Dict[str, Any]]:
        """
        Calcula indicadores técnicos basados en las velas almacenadas
        
        Returns:
            Diccionario con todos los indicadores calculados
        """
        try:
            # Obtener velas para cálculo (excluyendo la vela actual en curso)
            klines = self.klines_service.get_klines_for_calculation(
                symbol=symbol, 
                interval=interval, 
                limit=1000,  # Análisis más preciso con más datos históricos
                exclude_current=True
            )
            
            if len(klines) < 20:
                logger.error(f"❌ Insuficientes velas para cálculo: {len(klines)} (mínimo 20)")
                return None
                
            logger.info(f"📊 Calculando indicadores con {len(klines)} velas")
            
            # Calcular todos los indicadores
            indicators = self.indicators_calculator.calculate_all_indicators(klines)
            
            # Validar indicadores
            if not self.indicators_calculator.validate_indicators(indicators):
                logger.error("❌ Indicadores calculados no son válidos")
                return None
                
            # Agregar análisis de tendencia
            trend_analysis = self.indicators_calculator.get_trend_analysis(indicators)
            indicators["trend_analysis"] = trend_analysis
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculando indicadores: {e}")
            return None
            
    def _save_indicators_to_legacy_table(self, indicators: Dict[str, Any]) -> bool:
        """
        Guarda los indicadores en la tabla existente para compatibilidad
        """
        try:
            # Adaptar formato para la tabla existente
            adapted_data = {
                "timestamp": indicators["timestamp"].isoformat() if isinstance(indicators["timestamp"], datetime) else str(indicators["timestamp"]),
                "symbol": indicators.get("symbol", "BTCUSDT"),
                "interval": indicators.get("interval", "240"),
                "close_price": indicators.get("close_price"),
                "rsi": indicators.get("rsi14"),
                "sma": indicators.get("ema20"),  # Usar EMA20 como SMA para compatibilidad
                "adx": indicators.get("adx14"),
                "macd": indicators.get("macd"),
                "macd_signal": indicators.get("macd_signal"),
                "macd_hist": indicators.get("macd_histogram"),
                "bb_upper": indicators.get("bb_upper"),
                "bb_middle": indicators.get("bb_middle"),
                "bb_lower": indicators.get("bb_lower")
            }
            
            # Usar el método existente del db_manager
            success = self.db_manager.save_indicators(adapted_data, signal=False)
            
            if success:
                logger.info("✅ Indicadores guardados en tabla legacy")
            else:
                logger.warning("⚠️ Error guardando en tabla legacy")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error guardando en tabla legacy: {e}")
            return False
            
    def get_latest_indicators(self, symbol: str = "BTCUSDT") -> Optional[Dict[str, Any]]:
        """
        Obtiene los últimos indicadores calculados desde la base de datos
        
        Returns:
            Diccionario con los últimos indicadores o None
        """
        try:
            recent_data = self.db_manager.get_recent_indicators(symbol=symbol, limit=1)
            
            if recent_data:
                return dict(recent_data[0])
            else:
                logger.warning(f"⚠️ No se encontraron indicadores recientes para {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo últimos indicadores: {e}")
            return None
            
    def get_system_status(self, symbol: str = "BTCUSDT", interval: str = "240") -> Dict[str, Any]:
        """
        Obtiene el estado del sistema
        
        Returns:
            Diccionario con información del estado del sistema
        """
        try:
            status = {
                "system_initialized": False,
                "klines_count": 0,
                "latest_kline_time": None,
                "latest_indicators_time": None,
                "last_update": None
            }
            
            # Verificar cantidad de velas
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # Contar velas
                    cur.execute(
                        "SELECT COUNT(*) FROM klines WHERE symbol = %s AND interval_type = %s",
                        (symbol, interval)
                    )
                    status["klines_count"] = cur.fetchone()[0]
                    
                    # Última vela
                    cur.execute(
                        "SELECT MAX(open_time) FROM klines WHERE symbol = %s AND interval_type = %s",
                        (symbol, interval)
                    )
                    latest_time = cur.fetchone()[0]
                    if latest_time:
                        status["latest_kline_time"] = datetime.fromtimestamp(latest_time / 1000)
                        
            # Verificar últimos indicadores
            latest_indicators = self.get_latest_indicators(symbol)
            if latest_indicators:
                status["latest_indicators_time"] = latest_indicators.get("created_at")
                status["last_update"] = latest_indicators.get("timestamp")
                
            # Sistema inicializado si hay suficientes velas
            status["system_initialized"] = status["klines_count"] >= 20
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado del sistema: {e}")
            return {"error": str(e)}
            
    def run_full_update_cycle(self, symbol: str = "BTCUSDT", interval: str = "240") -> Dict[str, Any]:
        """
        Ejecuta un ciclo completo de actualización
        
        Returns:
            Diccionario con el resultado del ciclo
        """
        try:
            logger.info(f"🔄 Iniciando ciclo completo de actualización para {symbol} {interval}")
            
            start_time = datetime.now()
            
            # Verificar si el sistema está inicializado
            status = self.get_system_status(symbol, interval)
            
            if not status.get("system_initialized"):
                logger.info("🚀 Sistema no inicializado, ejecutando inicialización...")
                if not self.initialize_system(symbol, interval):
                    return {"success": False, "error": "Failed to initialize system"}
            else:
                # Actualizar datos
                indicators = self.update_data(symbol, interval)
                
                if not indicators:
                    return {"success": False, "error": "Failed to update indicators"}
                    
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Obtener estado final
            final_status = self.get_system_status(symbol, interval)
            latest_indicators = self.get_latest_indicators(symbol)
            
            result = {
                "success": True,
                "execution_time": execution_time,
                "system_status": final_status,
                "latest_indicators": latest_indicators,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Ciclo completo ejecutado en {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en ciclo completo: {e}")
            return {"success": False, "error": str(e)}