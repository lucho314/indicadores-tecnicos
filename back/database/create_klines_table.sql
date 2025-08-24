-- Migración para crear tabla de velas históricas (klines) de Bybit
-- Optimizada para consultas rápidas y ventana deslizante

CREATE TABLE IF NOT EXISTS klines (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    interval_type VARCHAR(10) NOT NULL,
    open_time BIGINT NOT NULL,
    close_time BIGINT NOT NULL,
    open_price DECIMAL(20, 8) NOT NULL,
    high_price DECIMAL(20, 8) NOT NULL,
    low_price DECIMAL(20, 8) NOT NULL,
    close_price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8) NOT NULL,
    turnover DECIMAL(20, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agregar constraint único si no existe
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'klines_symbol_interval_open_time_key'
    ) THEN
        ALTER TABLE klines ADD CONSTRAINT klines_symbol_interval_open_time_key 
        UNIQUE(symbol, interval_type, open_time);
    END IF;
END $$;

-- Índices para optimizar consultas
-- Índice principal para consultas por símbolo, intervalo y tiempo
CREATE INDEX IF NOT EXISTS idx_klines_symbol_interval_time 
    ON klines(symbol, interval_type, open_time DESC);

-- Índice para consultas de tiempo únicamente (útil para limpieza)
CREATE INDEX IF NOT EXISTS idx_klines_open_time 
    ON klines(open_time DESC);

-- Índice para consultas por close_time (útil para sincronización)
CREATE INDEX IF NOT EXISTS idx_klines_close_time 
    ON klines(close_time DESC);



-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at (solo si no existe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_klines_updated_at'
    ) THEN
        CREATE TRIGGER update_klines_updated_at
            BEFORE UPDATE ON klines
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Comentarios para documentación
COMMENT ON TABLE klines IS 'Tabla de velas históricas de Bybit para cálculo de indicadores técnicos';
COMMENT ON COLUMN klines.open_time IS 'Timestamp de apertura en milisegundos';
COMMENT ON COLUMN klines.close_time IS 'Timestamp de cierre en milisegundos';
COMMENT ON COLUMN klines.interval_type IS 'Tipo de intervalo: 240=4h, 60=1h, 15=15m, etc.';
COMMENT ON COLUMN klines.turnover IS 'Volumen en moneda base (USDT)';