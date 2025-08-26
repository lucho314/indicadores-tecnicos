from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import jwt
import psycopg2
import os
from config import API_KEY

# Configuración
SECRET_KEY = API_KEY
ALGORITHM = "HS256"

security = HTTPBearer()

class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    try:
        # Usar la variable de entorno DATABASE_URL si está disponible
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            return psycopg2.connect(database_url)
        else:
            # Configuración por defecto
            return psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'indicadores_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                port=os.getenv('DB_PORT', '5432')
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error conectando a la base de datos: {e}")

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica el token JWT"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(username: str = Depends(verify_token)):
    """Obtiene el usuario actual basado en el token"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, email, is_active, is_admin FROM users WHERE username = %s",
            (username,)
        )
        user_data = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        
        return User(
            id=user_data[0],
            username=user_data[1],
            email=user_data[2],
            is_active=user_data[3],
            is_admin=user_data[4]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo usuario: {e}"
        )