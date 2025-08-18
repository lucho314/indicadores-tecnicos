-- Crear tabla de indicadores con PostgreSQL
CREATE TABLE IF NOT EXISTS indicadores (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    interval_tf VARCHAR(10) NOT NULL,
    price DECIMAL(15,8),
    rsi DECIMAL(10,5),
    sma DECIMAL(15,8),
    adx DECIMAL(10,5),
    macd DECIMAL(15,8),
    macd_signal DECIMAL(15,8),
    macd_hist DECIMAL(15,8),
    bb_upper DECIMAL(15,8),
    bb_middle DECIMAL(15,8),
    bb_lower DECIMAL(15,8),
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_indicadores_symbol_timestamp ON indicadores(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicadores_timestamp ON indicadores(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_indicadores_symbol ON indicadores(symbol);

-- Crear tabla para logs de ejecución
CREATE TABLE IF NOT EXISTS execution_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    symbol VARCHAR(20),
    status VARCHAR(20),
    message TEXT,
    execution_time_seconds DECIMAL(10,3),
    error_details TEXT
);

CREATE INDEX IF NOT EXISTS idx_execution_logs_timestamp ON execution_logs(timestamp DESC);

-- Crear tabla de usuarios para la API
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
