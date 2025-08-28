from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.postgres_db_manager import PostgresIndicadorDB
from service.trading_strategy_service import TradingStrategyService
from service.bybit_service import BybitService

# Importar funciones de autenticación desde auth.py
from .auth import get_current_user, User

logger = logging.getLogger(__name__)

# Crear el router de FastAPI
router = APIRouter()

# Modelos Pydantic
class TradingStrategy(BaseModel):
    id: Optional[int] = None
    symbol: str
    action: str
    confidence: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    justification: Optional[str] = None
    key_factors: Optional[str] = None
    risk_level: Optional[str] = None
    executed: bool = False
    status: str = 'PENDING'
    transaction_id: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    llm_response: Optional[Dict[str, Any]] = None
    market_conditions: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None

class StrategyStats(BaseModel):
    total_strategies: int
    active_strategies: int
    expired_strategies: int
    executed_strategies: int
    pending_strategies: int
    success_rate: float

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    database_connected: bool
    service_version: str

class ExecuteStrategyRequest(BaseModel):
    strategy_id: int
    usdt_amount: float

# Variables globales para servicios
_db = None
_strategy_service = None
_bybit_service = None

def get_strategy_service():
    """Dependency para obtener el servicio de estrategias"""
    global _db, _strategy_service
    
    if _strategy_service is None:
        try:
            # Usar la variable de entorno DATABASE_URL si está disponible
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                _db = PostgresIndicadorDB(database_url=database_url)
            else:
                _db = PostgresIndicadorDB()
            _strategy_service = TradingStrategyService(_db)
            logger.info("✅ Servicios de trading strategies inicializados")
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios: {e}")
            raise HTTPException(status_code=500, detail="Servicio de estrategias no disponible")
    
    return _strategy_service

def get_bybit_service():
    """Dependency para obtener el servicio de Bybit"""
    global _bybit_service
    
    if _bybit_service is None:
        try:
            _bybit_service = BybitService()
            logger.info("✅ Servicio de Bybit inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando servicio de Bybit: {e}")
            raise HTTPException(status_code=500, detail="Servicio de Bybit no disponible")
    
    return _bybit_service

@router.post("/", response_model=Dict[str, Any])
async def create_strategy(
    strategy: TradingStrategy,
    service: TradingStrategyService = Depends(get_strategy_service)
):
    """
    Crea una nueva estrategia de trading
    """
    try:
        strategy_id = service.save_strategy(
            symbol=strategy.symbol,
            action=strategy.action,
            confidence=strategy.confidence,
            entry_price=strategy.entry_price,
            stop_loss=strategy.stop_loss,
            take_profit=strategy.take_profit,
            risk_reward_ratio=strategy.risk_reward_ratio,
            justification=strategy.justification,
            key_factors=strategy.key_factors,
            risk_level=strategy.risk_level,
            llm_response=strategy.llm_response,
            market_conditions=strategy.market_conditions
        )
        return {"strategy_id": strategy_id, "message": "Estrategia creada exitosamente"}
    except Exception as e:
        logger.error(f"Error creando estrategia: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active", response_model=List[TradingStrategy])
async def get_active_strategies(
    symbol: Optional[str] = None,
    service: TradingStrategyService = Depends(get_strategy_service)
):
    """
    Obtiene todas las estrategias activas (vigentes)
    
    - **symbol**: Filtrar por símbolo específico (opcional)
    """
    try:
        strategies = service.get_active_strategies(symbol)
        return [TradingStrategy(**strategy) for strategy in strategies]
    except Exception as e:
        logger.error(f"Error obteniendo estrategias activas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Verifica el estado del servicio de estrategias
    """
    try:
        database_connected = False
        service_available = False
        
        try:
            # Intentar obtener el servicio (esto inicializará la conexión si es necesario)
            service = get_strategy_service()
            service_available = True
            
            # Probar conexión a la base de datos
            if _db:
                conn = _db.get_connection()
                if conn:
                    conn.close()
                    database_connected = True
        except:
            pass
        
        return HealthCheck(
            status="healthy" if database_connected and service_available else "unhealthy",
            timestamp=datetime.now(),
            database_connected=database_connected,
            service_version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthCheck(
            status="unhealthy",
            timestamp=datetime.now(),
            database_connected=False,
            service_version="1.0.0"
        )

@router.get("/{strategy_id}", response_model=TradingStrategy)
async def get_strategy_by_id(
    strategy_id: int,
    service: TradingStrategyService = Depends(get_strategy_service)
):
    """
    Obtiene una estrategia específica por ID
    
    - **strategy_id**: ID de la estrategia
    """
    try:
        strategy = service.get_strategy_by_id(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Estrategia no encontrada")
        return TradingStrategy(**strategy)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estrategia {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{strategy_id}/status")
async def update_strategy_status(
    strategy_id: int,
    status: str,
    transaction_id: Optional[str] = None,
    service: TradingStrategyService = Depends(get_strategy_service)
):
    """
    Actualiza el estado de una estrategia
    
    - **strategy_id**: ID de la estrategia
    - **status**: Nuevo estado (PENDING, OPEN, CLOSED, CANCELLED, EXPIRED)
    - **transaction_id**: ID de transacción (opcional)
    """
    try:
        valid_statuses = ['PENDING', 'OPEN', 'CLOSED', 'CANCELLED', 'EXPIRED']
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400, 
                detail=f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}"
            )
        
        success = service.update_strategy_status(strategy_id, status, transaction_id)
        if not success:
            raise HTTPException(status_code=404, detail="Estrategia no encontrada")
        
        return {"message": "Estado actualizado correctamente", "strategy_id": strategy_id, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando estado de estrategia {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/summary", response_model=StrategyStats)
async def get_strategy_statistics(
    service: TradingStrategyService = Depends(get_strategy_service)
):
    """
    Obtiene estadísticas generales de las estrategias
    """
    try:
        stats = service.get_strategy_statistics()
        return StrategyStats(**stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/expire-old")
async def expire_old_strategies(
    service: TradingStrategyService = Depends(get_strategy_service)
):
    """
    Marca manualmente las estrategias expiradas
    """
    try:
        expired_count = service.expire_old_strategies()
        return {
            "message": "Estrategias expiradas procesadas",
            "expired_count": expired_count,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error expirando estrategias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute")
async def execute_strategy(
    request: ExecuteStrategyRequest,
    current_user: User = Depends(get_current_user),
    strategy_service: TradingStrategyService = Depends(get_strategy_service),
    bybit_service: BybitService = Depends(get_bybit_service)
):
    """
    Ejecuta una estrategia específica con la cantidad de USDT especificada
    
    - **strategy_id**: ID de la estrategia a ejecutar
    - **usdt_amount**: Cantidad de USDT a invertir
    
    Requiere autenticación de usuario.
    """
    try:
        # Obtener la estrategia de la base de datos
        strategy = strategy_service.get_strategy_by_id(request.strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Estrategia no encontrada")
        
        # Verificar que la estrategia esté activa
        if strategy.get('status') != 'PENDING':
            raise HTTPException(
                status_code=400, 
                detail=f"La estrategia no está en estado PENDING. Estado actual: {strategy.get('status')}"
            )
        
        # Verificar que la estrategia no haya expirado
        expires_at = strategy.get('expires_at')
        if expires_at and datetime.now() > expires_at:
            raise HTTPException(status_code=400, detail="La estrategia ha expirado")
        
        # Mapear la acción de la estrategia al formato de Bybit
        side = "Buy" if strategy.get('action') == 'LONG' else "Sell"
        
        # Ejecutar la estrategia usando el servicio de Bybit
        result = bybit_service.execute_strategy(
            symbol=strategy.get('symbol', 'BTCUSDT'),
            side=side,
            entry_price=strategy.get('entry_price'),
            take_profit=strategy.get('take_profit'),
            stop_loss=strategy.get('stop_loss'),
            average_price=strategy.get('entry_price'),  # Usar entry_price como average_price
            ticket=f"STRATEGY_{request.strategy_id}",
            usdt_amount=request.usdt_amount
        )
        
        # Solo actualizar el estado si la ejecución fue exitosa
        if result.get('success', False):
            # Marcar como OPEN con executed=true cuando se coloca exitosamente
            strategy_service.update_strategy_status(
                request.strategy_id, 
                'OPEN', 
                result.get('transaction_id'),
                executed_at=datetime.now()
            )
            logger.info(f"✅ Estrategia {request.strategy_id} ejecutada exitosamente por usuario {current_user.username}")
        else:
            logger.warning(f"⚠️ Estrategia {request.strategy_id} falló en ejecución: {result.get('error', 'Error desconocido')}")
        
        return {
            "message": "Estrategia ejecutada exitosamente",
            "strategy_id": request.strategy_id,
            "usdt_amount": request.usdt_amount,
            "execution_result": result,
            "executed_by": current_user.username,
            "executed_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando estrategia {request.strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando estrategia: {str(e)}")