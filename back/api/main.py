"""
API REST para consultar indicadores técnicos
"""
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
import logging
import asyncio
import json
from config import API_KEY

# Configuración
SECRET_KEY = API_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar servicio de Bybit
try:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from service.bybit_service import BybitService
    BYBIT_AVAILABLE = True
    logger.info("✅ BybitService importado correctamente")
except ImportError as e:
    logger.warning(f"❌ BybitService no disponible: {e}")
    BYBIT_AVAILABLE = False

# Importar funciones de autenticación
from .auth import get_current_user, User, verify_token, get_db_connection, security

# Importar rutas de trading strategies
try:
    from .trading_strategies_api import router as trading_strategies_router
    logger.info("✅ Trading strategies API importado correctamente")
except ImportError as e:
    logger.warning(f"❌ Trading strategies API no disponible: {e}")
    trading_strategies_router = None

app = FastAPI(
    title="Indicadores Técnicos API",
    description="API para consultar indicadores técnicos de criptomonedas",
    version="1.0.0"
)

# Registrar rutas de trading strategies
if trading_strategies_router:
    app.include_router(trading_strategies_router, prefix="/trading-strategies", tags=["Trading Strategies"])
    logger.info("✅ Rutas de trading strategies registradas")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# security se importa desde auth.py

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# User se importa desde auth.py

class SeedRequest(BaseModel):
    password: str
    username: Optional[str] = "admin"
    email: Optional[str] = "admin@indicadores.com"

class Indicador(BaseModel):
    id: int
    timestamp: datetime
    symbol: str
    interval_tf: str
    price: Optional[float]
    rsi: Optional[float]
    sma: Optional[float]
    adx: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_hist: Optional[float]
    bb_upper: Optional[float]
    bb_middle: Optional[float]
    bb_lower: Optional[float]
    signal: Optional[bool] = False
    created_at: datetime

class IndicadoresResponse(BaseModel):
    data: List[Indicador]
    total: int
    page: int
    per_page: int
    total_pages: int

# get_db_connection se importa desde auth.py

# JWT functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# verify_token y get_current_user se importan desde auth.py

# Routes
@app.get("/")
async def root():
    return {"message": "API de Indicadores Técnicos", "version": "1.0.0"}

@app.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, hashed_password, is_active FROM users WHERE username = %s",
            (login_data.username,)
        )
        user_data = cursor.fetchone()
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
        
        username, hashed_password, is_active = user_data
        
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo"
            )
        
        # Verificar contraseña
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), hashed_password.encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )
        
        # Crear token
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
        
    finally:
        conn.close()

@app.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/seed")
async def seed_database(seed_data: SeedRequest):
    """
    Crear usuario administrador en la base de datos
    Este endpoint carga los datos iniciales necesarios para el sistema
    
    Args:
        seed_data: Datos para crear el usuario admin (password, username, email)
    """
    try:
        # Conectar a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Crear tabla de usuarios si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Hashear contraseña para usuario admin
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(seed_data.password.encode('utf-8'), salt).decode('utf-8')
        
        # Insertar usuario admin
        cursor.execute("""
        INSERT INTO users (username, email, hashed_password, is_active, is_admin) 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (username) 
        DO UPDATE SET 
            hashed_password = EXCLUDED.hashed_password,
            email = EXCLUDED.email,
            is_active = EXCLUDED.is_active,
            is_admin = EXCLUDED.is_admin;
        """, (seed_data.username, seed_data.email, hashed_password, True, True))
        
        connection.commit()
        
        logger.info("✅ Usuario administrador creado exitosamente")
        
        return {
            "message": "Database seeded successfully",
            "users_created": [
                {
                    "username": seed_data.username,
                    "email": seed_data.email, 
                    "password": seed_data.password,
                    "is_admin": True
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error seeding database: {str(e)}"
        )
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

@app.get("/indicadores", response_model=IndicadoresResponse)
async def get_indicadores(
    page: int = 1,
    per_page: int = 50,
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Obtener indicadores con paginación y filtros
    """
    if per_page > 100:
        per_page = 100
    
    offset = (page - 1) * per_page
    
    # Construir query base
    where_conditions = []
    params = []
    
    if symbol:
        where_conditions.append("symbol = %s")
        params.append(symbol)
    
    if start_date:
        where_conditions.append("timestamp >= %s")
        params.append(start_date)
    
    if end_date:
        where_conditions.append("timestamp <= %s")
        params.append(end_date)
    
    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Contar total de registros
        count_query = f"SELECT COUNT(*) FROM indicadores {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Obtener datos paginados
        data_query = f"""
        SELECT id, timestamp, symbol, interval_tf, price, rsi, sma, adx, 
               macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, created_at
        FROM indicadores 
        {where_clause}
        ORDER BY timestamp DESC 
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(data_query, params + [per_page, offset])
        rows = cursor.fetchall()
        
        indicadores = []
        for row in rows:
            indicadores.append(Indicador(
                id=row[0],
                timestamp=row[1],
                symbol=row[2],
                interval_tf=row[3],
                price=row[4],
                rsi=row[5],
                sma=row[6],
                adx=row[7],
                macd=row[8],
                macd_signal=row[9],
                macd_hist=row[10],
                bb_upper=row[11],
                bb_middle=row[12],
                bb_lower=row[13],
                created_at=row[14]
            ))
        
        total_pages = (total + per_page - 1) // per_page
        
        return IndicadoresResponse(
            data=indicadores,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    finally:
        conn.close()

@app.get("/indicators")
async def get_indicators(page: int = 1, limit: int = 10, search: Optional[str] = None):
    offset = (page - 1) * limit

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Contar total de registros basado en la búsqueda
        if search:
            cursor.execute("SELECT COUNT(*) FROM indicadores WHERE symbol ILIKE %s", (f"%{search}%",))
            total_result = cursor.fetchone()
            total = total_result[0] if total_result and total_result[0] is not None else 0
            
            # Obtener datos paginados con búsqueda
            cursor.execute(
            """
            SELECT id, timestamp, symbol, interval_tf, price, rsi, sma, adx, 
                   macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, signal, created_at
            FROM indicadores
            WHERE symbol ILIKE %s
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
            """,
            (f"%{search}%", limit, offset),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM indicadores")
            total_result = cursor.fetchone()
            total = total_result[0] if total_result and total_result[0] is not None else 0
            
            # Obtener datos paginados sin búsqueda
            cursor.execute(
            """
            SELECT id, timestamp, symbol, interval_tf, price, rsi, sma, adx, 
                   macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, signal, created_at
            FROM indicadores
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
            )
        rows = cursor.fetchall()

        # Formatear los datos
        indicators = [
            {
                "id": row[0],
                "timestamp": row[1],
                "symbol": row[2],
                "interval_tf": row[3],
                "price": row[4],
                "rsi": row[5],
                "sma": row[6],
                "adx": row[7],
                "macd": row[8],
                "macd_signal": row[9],
                "macd_hist": row[10],
                "bb_upper": row[11],
                "bb_middle": row[12],
                "bb_lower": row[13],
                "signal": row[14],
                "created_at": row[15],
            }
            for row in rows
        ]

        return {
            "data": indicators,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit,
        }
    finally:
        conn.close()

@app.get("/symbols")
async def get_symbols():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT symbol FROM indicadores ORDER BY symbol")
        symbols = [row[0] for row in cursor.fetchall() if row[0] is not None]
        return symbols
    finally:
        conn.close()

@app.get("/stats")
async def get_stats():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Total de símbolos
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM indicadores")
        total_symbols = cursor.fetchone()
        total_symbols = total_symbols[0] if total_symbols and total_symbols[0] is not None else 0

        # Promedio de precio de BTC/USD
        cursor.execute("SELECT AVG(price) FROM indicadores WHERE symbol = 'BTC/USD'")
        avg_btc_price = cursor.fetchone()
        avg_btc_price = avg_btc_price[0] if avg_btc_price and avg_btc_price[0] is not None else 0

        # Promedio de precio de ETH/USD
        cursor.execute("SELECT AVG(price) FROM indicadores WHERE symbol = 'ETH/USD'")
        avg_eth_price = cursor.fetchone()
        avg_eth_price = avg_eth_price[0] if avg_eth_price and avg_eth_price[0] is not None else 0

        # Promedio de precio de BNB/USD
        cursor.execute("SELECT AVG(price) FROM indicadores WHERE symbol = 'BNB/USD'")
        avg_bnb_price = cursor.fetchone()
        avg_bnb_price = avg_bnb_price[0] if avg_bnb_price and avg_bnb_price[0] is not None else 0

        # Promedio de RSI para BTC
        cursor.execute("SELECT AVG(rsi) FROM indicadores WHERE symbol = 'BTC/USD'")
        avg_btc_rsi = cursor.fetchone()
        avg_btc_rsi = avg_btc_rsi[0] if avg_btc_rsi and avg_btc_rsi[0] is not None else 0

        # Promedio de RSI para ETH
        cursor.execute("SELECT AVG(rsi) FROM indicadores WHERE symbol = 'ETH/USD'")
        avg_eth_rsi = cursor.fetchone()
        avg_eth_rsi = avg_eth_rsi[0] if avg_eth_rsi and avg_eth_rsi[0] is not None else 0

        # Promedio de RSI para BNB
        cursor.execute("SELECT AVG(rsi) FROM indicadores WHERE symbol = 'BNB/USD'")
        avg_bnb_rsi = cursor.fetchone()
        avg_bnb_rsi = avg_bnb_rsi[0] if avg_bnb_rsi and avg_bnb_rsi[0] is not None else 0

        # Promedio de RSI general
        cursor.execute("SELECT AVG(rsi) FROM indicadores")
        avg_rsi = cursor.fetchone()
        avg_rsi = avg_rsi[0] if avg_rsi and avg_rsi[0] is not None else 0

        # Señales activas (ejemplo: RSI > 70 o RSI < 30)
        cursor.execute("SELECT COUNT(*) FROM indicadores WHERE rsi > 70 OR rsi < 30")
        active_signals = cursor.fetchone()
        active_signals = active_signals[0] if active_signals and active_signals[0] is not None else 0

        # Señales activas por el LLM (signal = true)
        cursor.execute("SELECT COUNT(*) FROM indicadores WHERE signal = true")
        llm_signals = cursor.fetchone()
        llm_signals = llm_signals[0] if llm_signals and llm_signals[0] is not None else 0

        # Cambios de precio y RSI para BTC (últimos 24h)
        cursor.execute(
            """
            SELECT 
                (MAX(price) - MIN(price)) / MIN(price) * 100 AS price_change,
                (MAX(rsi) - MIN(rsi)) AS rsi_change
            FROM indicadores
            WHERE timestamp >= NOW() - INTERVAL '24 HOURS' AND symbol = 'BTC/USD'
            """
        )
        btc_changes = cursor.fetchone()
        btc_price_change = btc_changes[0] if btc_changes and btc_changes[0] is not None else 0
        btc_rsi_change = btc_changes[1] if btc_changes and btc_changes[1] is not None else 0

        # Cambios de precio y RSI para ETH (últimos 24h)
        cursor.execute(
            """
            SELECT 
                (MAX(price) - MIN(price)) / MIN(price) * 100 AS price_change,
                (MAX(rsi) - MIN(rsi)) AS rsi_change
            FROM indicadores
            WHERE timestamp >= NOW() - INTERVAL '24 HOURS' AND symbol = 'ETH/USD'
            """
        )
        eth_changes = cursor.fetchone()
        eth_price_change = eth_changes[0] if eth_changes and eth_changes[0] is not None else 0
        eth_rsi_change = eth_changes[1] if eth_changes and eth_changes[1] is not None else 0

        # Cambios de precio y RSI para BNB (últimos 24h)
        cursor.execute(
            """
            SELECT 
                (MAX(price) - MIN(price)) / MIN(price) * 100 AS price_change,
                (MAX(rsi) - MIN(rsi)) AS rsi_change
            FROM indicadores
            WHERE timestamp >= NOW() - INTERVAL '24 HOURS' AND symbol = 'BNB/USD'
            """
        )
        bnb_changes = cursor.fetchone()
        bnb_price_change = bnb_changes[0] if bnb_changes and bnb_changes[0] is not None else 0
        bnb_rsi_change = bnb_changes[1] if bnb_changes and bnb_changes[1] is not None else 0

        # Cambios generales (últimos 24h)
        cursor.execute(
            """
            SELECT 
                (MAX(price) - MIN(price)) / MIN(price) * 100 AS price_change,
                (MAX(rsi) - MIN(rsi)) AS rsi_change
            FROM indicadores
            WHERE timestamp >= NOW() - INTERVAL '24 HOURS'
            """
        )
        changes = cursor.fetchone()
        price_change = changes[0] if changes and changes[0] is not None else 0
        rsi_change = changes[1] if changes and changes[1] is not None else 0

        return {
            "totalSymbols": total_symbols,
            "avgBtcPrice": round(float(avg_btc_price), 2),
            "avgEthPrice": round(float(avg_eth_price), 2),
            "avgBnbPrice": round(float(avg_bnb_price), 2),
            "avgBtcRsi": round(float(avg_btc_rsi), 2),
            "avgEthRsi": round(float(avg_eth_rsi), 2),
            "avgBnbRsi": round(float(avg_bnb_rsi), 2),
            "avgRsi": round(float(avg_rsi), 2),
            "activeSignals": active_signals,
            "llmSignals": llm_signals,
            "btcPriceChange": round(float(btc_price_change), 2),
            "btcRsiChange": round(float(btc_rsi_change), 2),
            "ethPriceChange": round(float(eth_price_change), 2),
            "ethRsiChange": round(float(eth_rsi_change), 2),
            "bnbPriceChange": round(float(bnb_price_change), 2),
            "bnbRsiChange": round(float(bnb_rsi_change), 2),
            "priceChange": round(float(price_change), 2),
            "rsiChange": round(float(rsi_change), 2),
        }
    finally:
        conn.close()

# @app.get("/debug/bybit")
# async def debug_bybit():
#     """
#     Endpoint temporal para debugging de credenciales Bybit
#     """
#     try:
#         import os
#         from config import BYBIT_API_KEY, BYBIT_API_SECRET
        
#         return {
#             "config_api_key": BYBIT_API_KEY[:10] + "..." if BYBIT_API_KEY else None,
#             "config_api_secret": BYBIT_API_SECRET[:10] + "..." if BYBIT_API_SECRET else None,
#             "env_api_key": os.getenv('BYBIT_API_KEY', 'No encontrada')[:10] + "..." if os.getenv('BYBIT_API_KEY') else "No encontrada",
#             "env_api_secret": os.getenv('BYBIT_API_SECRET', 'No encontrada')[:10] + "..." if os.getenv('BYBIT_API_SECRET') else "No encontrada",
#             "bybit_available": BYBIT_AVAILABLE
#         }
#     except Exception as e:
#         return {"error": str(e)}

@app.get("/positions")
async def get_open_positions():
    """
    Obtiene las posiciones abiertas en los principales pares de trading
    """
    try:
        logger.info(f"🔍 Endpoint /positions llamado. BYBIT_AVAILABLE: {BYBIT_AVAILABLE}")
        
        if not BYBIT_AVAILABLE:
            logger.warning("❌ Bybit no disponible, devolviendo respuesta mock")
            return {
                "success": False,
                "totalOpenPositions": 0,
                "availableBalance": 0,
                "positions": {
                    "BTCUSDT": None,
                    "ETHUSDT": None,
                    "BNBUSDT": None
                },
                "timestamp": datetime.now().isoformat(),
                "message": "Servicio Bybit no disponible"
            }

        logger.info("🚀 Creando instancia de BybitService...")
        # Crear instancia del servicio
        bybit_service = BybitService()
        logger.info("✅ BybitService creado exitosamente")
        
        # Probar conexión primero
        logger.info("🧪 Probando conexión con Bybit...")
        if not bybit_service.test_connection():
            logger.error("❌ Falló la prueba de conexión")
            return {
                "success": False,
                "totalOpenPositions": 0,
                "availableBalance": 0,
                "positions": {
                    "BTCUSDT": None,
                    "ETHUSDT": None,
                    "BNBUSDT": None
                },
                "timestamp": datetime.now().isoformat(),
                "message": "Error de conexión con Bybit"
            }
        
        logger.info("💰 Obteniendo balance disponible...")
        # Obtener balance disponible
        balance_info = bybit_service.get_available_balance()
        available_balance = balance_info.get('transferBalance', 0)
        logger.info(f"✅ Balance obtenido: {available_balance}")
        
        # Verificar posiciones en los principales pares
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
        positions = {}
        total_open_positions = 0
        
        for symbol in symbols:
            try:
                logger.info(f"📊 Verificando posición para {symbol}...")
                position = bybit_service.get_open_position(symbol)
                if position:
                    logger.info(f"✅ Posición encontrada para {symbol}")
                    positions[symbol] = {
                        "symbol": symbol,
                        "side": position.get('side'),
                        "size": float(position.get('size', 0)),
                        "avgPrice": float(position.get('avgPrice', 0)),
                        "markPrice": float(position.get('markPrice', 0)),
                        "unrealisedPnl": float(position.get('unrealisedPnl', 0)),
                        "leverage": position.get('leverage'),
                        "positionValue": float(position.get('positionValue', 0))
                    }
                    total_open_positions += 1
                else:
                    logger.info(f"ℹ️ No hay posición para {symbol}")
                    positions[symbol] = None
            except Exception as e:
                logger.error(f"❌ Error obteniendo posición para {symbol}: {e}")
                positions[symbol] = {"error": str(e)}
        
        logger.info(f"🎉 Proceso completado. Total posiciones: {total_open_positions}")
        return {
            "success": True,
            "totalOpenPositions": total_open_positions,
            "availableBalance": available_balance,
            "balanceInfo": balance_info,
            "positions": positions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"💥 Error obteniendo posiciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo posiciones: {str(e)}")


@app.get("/price")
async def get_price(symbol: str):
    """
    Obtiene el precio actual de un par de trading.
    
    Args:
        symbol: El símbolo del par (ej: 'BTCUSDT')
    
    Returns:
        Un diccionario con el precio actual o un mensaje de error.
    """
    try:
        logger.info(f"🔍 Endpoint /price llamado con símbolo: {symbol}")
        
        if not BYBIT_AVAILABLE:
            logger.warning("❌ Bybit no disponible, devolviendo respuesta mock")
            return {
                "success": False,
                "symbol": symbol,
                "price": None,
                "message": "Servicio Bybit no disponible"
            }
        
        # Crear instancia del servicio Bybit
        bybit_service = BybitService()
        
        # Obtener el precio del par
        price = bybit_service.get_price(symbol)
        if price is not None:
            logger.info(f"✅ Precio obtenido para {symbol}: {price}")
            return {
                "success": True,
                "symbol": symbol,
                "price": price
            }
        else:
            logger.warning(f"⚠️ No se pudo obtener el precio para {symbol}")
            return {
                "success": False,
                "symbol": symbol,
                "price": None,
                "message": f"No se pudo obtener el precio para {symbol}"
            }
    except Exception as e:
        logger.error(f"💥 Error obteniendo precio para {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo precio para {symbol}: {str(e)}")


# Clase para manejar conexiones WebSocket
class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remover conexiones inactivas
                self.active_connections.remove(connection)

manager = WebSocketManager()

@app.websocket("/ws/positions/{symbol}")
async def websocket_positions(websocket: WebSocket, symbol: str):
    """
    WebSocket para obtener el estado de posiciones en tiempo real desde Bybit.
    Requiere autenticación Bearer token.
    
    Args:
        websocket: La conexión WebSocket
        symbol: El símbolo del par (ej: 'BTCUSDT')
    """
    # Verificar autenticación antes de aceptar la conexión
    try:
        # Obtener el token del query parameter o headers
        token = None
        
        # Buscar token en query parameters
        query_params = dict(websocket.query_params)
        if "token" in query_params:
            token = query_params["token"]
        
        # Si no hay token en query params, buscar en headers
        if not token:
            headers = dict(websocket.headers)
            auth_header = headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remover "Bearer "
        
        if not token:
            await websocket.close(code=4001, reason="Token de autenticación requerido")
            return
        
        # Verificar el token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                await websocket.close(code=4002, reason="Token inválido")
                return
        except jwt.PyJWTError:
            await websocket.close(code=4003, reason="Token inválido o expirado")
            return
        
        # Si llegamos aquí, el token es válido
        await manager.connect(websocket)
        logger.info(f"🔌 Cliente autenticado ({username}) conectado al WebSocket para {symbol}")
        
    except Exception as e:
        logger.error(f"❌ Error en autenticación WebSocket: {e}")
        await websocket.close(code=4000, reason="Error en autenticación")
        return
    
    try:
        if not BYBIT_AVAILABLE:
            await websocket.send_text(json.dumps({
                "error": "Servicio Bybit no disponible",
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }))
            return
        
        # Crear instancia del servicio Bybit
        bybit_service = BybitService()
        
        while True:
            try:
                # Obtener posición actual
                position = bybit_service.get_open_position(symbol)
                
                # Obtener balance disponible
                balance = bybit_service.get_available_balance()
                
                # Obtener precio actual
                current_price = bybit_service.get_price(symbol)
                
                # Preparar datos para enviar
                data = {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "position": position,
                    "balance": balance,
                    "current_price": current_price,
                    "has_position": position is not None and float(position.get('size', 0)) != 0
                }
                
                # Enviar datos al cliente
                await websocket.send_text(json.dumps(data, default=str))
                
                # Esperar 5 segundos antes de la siguiente actualización
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Error obteniendo datos de Bybit: {e}")
                error_data = {
                    "error": f"Error obteniendo datos: {str(e)}",
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(error_data))
                await asyncio.sleep(10)  # Esperar más tiempo en caso de error
                
    except WebSocketDisconnect:
        logger.info(f"🔌 Cliente desconectado del WebSocket para {symbol}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
        manager.disconnect(websocket)


@app.get("/indicators/{symbol}")
async def get_technical_indicators(symbol: str, interval: str = "240"):
    """
    Obtiene los indicadores técnicos para un símbolo específico directamente desde Bybit.
    
    Args:
        symbol: El símbolo del par (ej: 'BTCUSDT')
        interval: Intervalo en minutos (240=4h, 60=1h, por defecto 240)
    
    Returns:
        Un diccionario con todos los indicadores técnicos calculados.
    """
    try:
        logger.info(f"🔍 Endpoint /indicators/{symbol} llamado con intervalo: {interval}")
        
        # Importar servicios necesarios
        from service.klines_service import KlinesService
        from service.technical_indicators import TechnicalIndicatorsCalculator
        
        # Obtener datos frescos directamente de Bybit
        klines_service = KlinesService()
        indicators_calculator = TechnicalIndicatorsCalculator()
        
        # Obtener las últimas 1000 velas directamente de la API para análisis más preciso
        klines = klines_service.fetch_klines_from_api(symbol=symbol, interval=interval, limit=1000)
        
        if len(klines) < 20:
            logger.error(f"❌ Insuficientes velas para cálculo: {len(klines)} (mínimo 20)")
            return {
                "success": False,
                "symbol": symbol,
                "interval": interval,
                "error": f"Insuficientes datos: {len(klines)} velas (mínimo 20)",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"📊 Calculando indicadores con {len(klines)} velas frescas de Bybit")
        
        # Calcular indicadores con datos frescos
        indicators = indicators_calculator.calculate_all_indicators(klines)
        
        if indicators and indicators_calculator.validate_indicators(indicators):
            logger.info(f"✅ Indicadores calculados para {symbol} - Precio: ${indicators.get('close_price', 0):.2f}")
            return {
                "success": True,
                "symbol": symbol,
                "interval": interval,
                "data": indicators,
                "timestamp": datetime.now().isoformat(),
                "data_source": "bybit_live_api",
                "klines_count": len(klines)
            }
        else:
            logger.warning(f"⚠️ Error calculando indicadores para {symbol}")
            return {
                "success": False,
                "symbol": symbol,
                "interval": interval,
                "error": "Error en cálculo de indicadores",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"💥 Error obteniendo indicadores para {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo indicadores para {symbol}: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
