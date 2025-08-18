"""
Script para crear el usuario administrador con contraseña hasheada
"""
import bcrypt
import psycopg2
import os

def hash_password(password: str) -> str:
    """Hashear una contraseña usando bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_admin_user():
    """Crear usuario administrador en la base de datos"""
    try:
        # Conectar a la base de datos
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "indicadores_db"),
            user=os.getenv("DB_USER", "indicadores_user"),
            password=os.getenv("DB_PASSWORD", "indicadores_pass123")
        )
        
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
        
        # Hashear contraseña
        password = "admin123"
        hashed_password = hash_password(password)
        
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
        """, ('admin', 'admin@indicadores.com', hashed_password, True, True))
        
        connection.commit()
        
        print("✅ Usuario administrador creado exitosamente")
        print("👤 Usuario: admin")
        print("🔑 Contraseña: admin123")
        print("📧 Email: admin@indicadores.com")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    create_admin_user()
