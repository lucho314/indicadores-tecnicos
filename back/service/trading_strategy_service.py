from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import logging
from database.postgres_db_manager import PostgresIndicadorDB

logger = logging.getLogger(__name__)

class TradingStrategyService:
    """Servicio para gestionar estrategias de trading del LLM"""
    
    def __init__(self, db: PostgresIndicadorDB):
        self.db = db
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Asegura que la tabla de estrategias existe"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Verificar si la tabla existe
                    query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'trading_strategies'
                    );
                    """
                    cur.execute(query)
                    result = cur.fetchone()
                    
                    if not result or not result[0]:
                        logger.info("Tabla trading_strategies no existe, creándola...")
                        self._create_table()
                    else:
                        logger.debug("Tabla trading_strategies ya existe")
                
        except Exception as e:
            logger.error(f"Error verificando tabla trading_strategies: {e}")
            raise
    
    def _create_table(self):
        """Crea la tabla de estrategias ejecutando el script SQL"""
        try:
            import os
            script_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'database', 
                'create_trading_strategies_table.sql'
            )
            
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                
                # Ejecutar el script completo
                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql_script)
                        conn.commit()
                        
                logger.info("Tabla trading_strategies creada exitosamente")
            else:
                logger.error(f"Script SQL no encontrado: {script_path}")
                raise FileNotFoundError(f"Script SQL no encontrado: {script_path}")
                
        except Exception as e:
            logger.error(f"Error creando tabla trading_strategies: {e}")
            raise
    
    def save_strategy(
        self, 
        symbol: str,
        action: str,
        confidence: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None,
        justification: Optional[str] = None,
        key_factors: Optional[str] = None,
        risk_level: Optional[str] = None,
        llm_response: Optional[Dict] = None,
        market_conditions: Optional[Dict] = None
    ) -> int:
        """Guarda una nueva estrategia de trading
        
        Args:
            symbol: Símbolo del activo (ej: BTCUSDT)
            action: Acción SHORT o LONG
            confidence: Nivel de confianza (0-100)
            entry_price: Precio de entrada
            stop_loss: Precio de stop loss
            take_profit: Precio de take profit
            risk_reward_ratio: Ratio riesgo/recompensa
            justification: Justificación de la estrategia
            key_factors: Factores clave considerados
            risk_level: Nivel de riesgo (LOW, MEDIUM, HIGH)
            llm_response: Respuesta completa del LLM
            market_conditions: Condiciones del mercado
            
        Returns:
            ID de la estrategia creada
        """
        try:
            # Validar acción
            if action not in ['SHORT', 'LONG']:
                raise ValueError(f"Acción inválida: {action}. Debe ser SHORT o LONG")
            
            # Validar confianza
            if not 0 <= confidence <= 100:
                raise ValueError(f"Confianza inválida: {confidence}. Debe estar entre 0 y 100")
            
            # Calcular fecha de expiración (1 hora)
            expires_at = datetime.now() + timedelta(hours=1)
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                    INSERT INTO trading_strategies (
                        symbol, action, confidence, entry_price, stop_loss, take_profit,
                        risk_reward_ratio, justification, key_factors, risk_level,
                        expires_at, llm_response, market_conditions
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) RETURNING id;
                    """
                    
                    params = (
                        symbol,
                        action,
                        confidence,
                        entry_price,
                        stop_loss,
                        take_profit,
                        risk_reward_ratio,
                        justification,
                        key_factors,
                        risk_level,
                        expires_at,
                        json.dumps(llm_response) if llm_response else None,
                        json.dumps(market_conditions) if market_conditions else None
                    )
                    
                    cur.execute(query, params)
                    result = cur.fetchone()
                    conn.commit()
                    
                    strategy_id = result[0] if result else None
                    
                    if strategy_id:
                        logger.info(f"Estrategia guardada exitosamente: ID {strategy_id}, {action} {symbol} @ {entry_price}")
                        return strategy_id
                    else:
                        raise Exception("No se pudo obtener el ID de la estrategia creada")
                
        except Exception as e:
            logger.error(f"Error guardando estrategia: {e}")
            raise
    
    def get_active_strategies(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene estrategias activas (vigentes)
        
        Args:
            symbol: Filtrar por símbolo específico (opcional)
            
        Returns:
            Lista de estrategias activas
        """
        try:
            # Primero expirar estrategias vencidas
            self.expire_old_strategies()
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM active_trading_strategies where status = 'PENDING'"
                    params = None
                    
                    if symbol:
                        query += " and symbol = %s"
                        params = (symbol,)
                    
                    cur.execute(query, params)
                    result = cur.fetchall()
                    
                    if not result:
                        return []
                    
                    # Convertir resultado a lista de diccionarios
                    columns = [
                        'id', 'symbol', 'action', 'confidence', 'entry_price', 'stop_loss',
                        'take_profit', 'risk_reward_ratio', 'justification', 'key_factors',
                        'risk_level', 'executed', 'status', 'transaction_id', 'created_at',
                        'expires_at', 'executed_at', 'closed_at', 'minutes_until_expiry',
                        'llm_response', 'market_conditions'
                    ]
                    
                    strategies = []
                    for row in result:
                        strategy = dict(zip(columns, row))
                        
                        # Parsear JSON fields
                        if strategy['llm_response']:
                            try:
                                strategy['llm_response'] = json.loads(strategy['llm_response'])
                            except:
                                pass
                                
                        if strategy['market_conditions']:
                            try:
                                strategy['market_conditions'] = json.loads(strategy['market_conditions'])
                            except:
                                pass
                        
                        strategies.append(strategy)
                    
                    logger.debug(f"Obtenidas {len(strategies)} estrategias activas")
                    return strategies
            
        except Exception as e:
            logger.error(f"Error obteniendo estrategias activas: {e}")
            raise
    
    def get_strategy_by_id(self, strategy_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene una estrategia por su ID"""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    query = "SELECT * FROM trading_strategies WHERE id = %s"
                    cur.execute(query, (strategy_id,))
                    result = cur.fetchone()
                    
                    if not result:
                        return None
                    
                    # Convertir a diccionario
                    columns = [
                        'id', 'symbol', 'action', 'confidence', 'entry_price', 'stop_loss',
                        'take_profit', 'risk_reward_ratio', 'justification', 'key_factors',
                        'risk_level', 'executed', 'status', 'transaction_id', 'created_at',
                        'expires_at', 'executed_at', 'closed_at', 'llm_response', 
                        'market_conditions', 'updated_at'
                    ]
                    
                    strategy = dict(zip(columns, result))
                    
                    # Parsear JSON fields
                    if strategy['llm_response']:
                        try:
                            strategy['llm_response'] = json.loads(strategy['llm_response'])
                        except:
                            pass
                            
                    if strategy['market_conditions']:
                        try:
                            strategy['market_conditions'] = json.loads(strategy['market_conditions'])
                        except:
                            pass
                    
                    return strategy
            
        except Exception as e:
            logger.error(f"Error obteniendo estrategia {strategy_id}: {e}")
            raise
    
    def update_strategy_status(
        self, 
        strategy_id: int, 
        status: str, 
        transaction_id: Optional[str] = None,
        executed_at: Optional[datetime] = None,
        closed_at: Optional[datetime] = None
    ) -> bool:
        """Actualiza el estado de una estrategia
        
        Args:
            strategy_id: ID de la estrategia
            status: Nuevo estado (PENDING, OPEN, CLOSED, CANCELLED, EXPIRED)
            transaction_id: ID de transacción de Bybit
            executed_at: Timestamp de ejecución
            closed_at: Timestamp de cierre
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            # Validar estado
            valid_statuses = ['PENDING', 'OPEN', 'CLOSED', 'CANCELLED', 'EXPIRED']
            if status not in valid_statuses:
                raise ValueError(f"Estado inválido: {status}. Debe ser uno de {valid_statuses}")
            
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Construir query dinámicamente
                    set_clauses = ['status = %s']
                    params = [status]
                    
                    if transaction_id is not None:
                        set_clauses.append('transaction_id = %s')
                        params.append(transaction_id)
                    
                    if executed_at is not None:
                        set_clauses.append('executed_at = %s')
                        set_clauses.append('executed = TRUE')
                        params.append(executed_at)
                    
                    if closed_at is not None:
                        set_clauses.append('closed_at = %s')
                        params.append(closed_at)
                    
                    params.append(strategy_id)
                    
                    query = f"""
                    UPDATE trading_strategies 
                    SET {', '.join(set_clauses)}
                    WHERE id = %s
                    """
                    
                    cur.execute(query, params)
                    conn.commit()
                    
                    logger.info(f"Estrategia {strategy_id} actualizada a estado {status}")
                    return True
            
        except Exception as e:
            logger.error(f"Error actualizando estrategia {strategy_id}: {e}")
            raise
    
    def expire_old_strategies(self) -> int:
        """Marca como expiradas las estrategias vencidas
        
        Returns:
            Número de estrategias expiradas
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    query = "SELECT expire_old_strategies()"
                    cur.execute(query)
                    result = cur.fetchone()
                    conn.commit()
                    
                    expired_count = result[0] if result else 0
                    
                    if expired_count > 0:
                        logger.info(f"Expiradas {expired_count} estrategias vencidas")
                    
                    return expired_count
            
        except Exception as e:
            logger.error(f"Error expirando estrategias: {e}")
            raise
    
    def get_strategy_statistics(self, symbol: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Obtiene estadísticas de estrategias
        
        Args:
            symbol: Filtrar por símbolo (opcional)
            days: Número de días hacia atrás para las estadísticas
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    base_query = """
                    SELECT 
                        COUNT(*) as total_strategies,
                        COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_strategies,
                        COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_strategies,
                        COUNT(CASE WHEN status = 'EXPIRED' THEN 1 END) as expired_strategies,
                        COUNT(CASE WHEN executed = TRUE THEN 1 END) as executed_strategies,
                        COUNT(CASE WHEN action = 'LONG' THEN 1 END) as long_strategies,
                        COUNT(CASE WHEN action = 'SHORT' THEN 1 END) as short_strategies,
                        AVG(confidence) as avg_confidence,
                        AVG(risk_reward_ratio) as avg_risk_reward
                    FROM trading_strategies 
                    WHERE created_at >= NOW() - INTERVAL '%s days'
                    """
                    
                    params = [days]
                    
                    if symbol:
                        base_query += " AND symbol = %s"
                        params.append(symbol)
                    
                    cur.execute(base_query, params)
                    result = cur.fetchone()
                    
                    if not result:
                        return {}
                    
                    columns = [
                        'total_strategies', 'open_strategies', 'closed_strategies',
                        'expired_strategies', 'executed_strategies', 'long_strategies',
                        'short_strategies', 'avg_confidence', 'avg_risk_reward'
                    ]
                    
                    stats = dict(zip(columns, result))
                    
                    # Convertir Decimal a float para JSON serialization
                    for key, value in stats.items():
                        if value is not None and hasattr(value, '__float__'):
                            stats[key] = float(value)
                    
                    # Mapear a la estructura esperada por StrategyStats
                    mapped_stats = {
                        'total_strategies': int(stats.get('total_strategies', 0)),
                        'active_strategies': int(stats.get('open_strategies', 0)),
                        'expired_strategies': int(stats.get('expired_strategies', 0)),
                        'executed_strategies': int(stats.get('executed_strategies', 0)),
                        'pending_strategies': int(stats.get('total_strategies', 0) - stats.get('executed_strategies', 0)),
                        'success_rate': float(stats.get('executed_strategies', 0) / max(stats.get('total_strategies', 1), 1) * 100)
                    }
                    
                    return mapped_stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            raise