-- Migración para crear tabla de estrategias de trading del LLM
-- Almacena las estrategias generadas por el LLM con vigencia de 1 hora

CREATE TABLE IF NOT EXISTS trading_strategies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('SHORT', 'LONG')),
    confidence DECIMAL(5, 2) NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    entry_price DECIMAL(20, 8) NOT NULL,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    risk_reward_ratio DECIMAL(10, 4),
    justification TEXT,
    key_factors TEXT,
    risk_level VARCHAR(10) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    
    -- Control de ejecución
    executed BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'OPEN', 'CLOSED', 'CANCELLED', 'EXPIRED')),
    transaction_id VARCHAR(100), -- ID de transacción de Bybit (futuro)
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL, -- Estrategia válida por 1 hora
    executed_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- Metadatos
    llm_response JSONB, -- Respuesta completa del LLM
    market_conditions JSONB, -- Condiciones del mercado al momento de creación
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_trading_strategies_symbol_created 
    ON trading_strategies(symbol, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_trading_strategies_status_expires 
    ON trading_strategies(status, expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_trading_strategies_active 
    ON trading_strategies(symbol, status, expires_at) 
    WHERE status IN ('PENDING', 'OPEN');

CREATE INDEX IF NOT EXISTS idx_trading_strategies_transaction 
    ON trading_strategies(transaction_id) 
    WHERE transaction_id IS NOT NULL;

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_trading_strategies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear trigger solo si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_trading_strategies_updated_at'
    ) THEN
        CREATE TRIGGER update_trading_strategies_updated_at
            BEFORE UPDATE ON trading_strategies
            FOR EACH ROW
            EXECUTE FUNCTION update_trading_strategies_updated_at();
    END IF;
END $$;

-- Función para marcar estrategias expiradas automáticamente
CREATE OR REPLACE FUNCTION expire_old_strategies()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE trading_strategies 
    SET status = 'EXPIRED', updated_at = CURRENT_TIMESTAMP
    WHERE status IN ('PENDING', 'OPEN') 
    AND expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Vista para estrategias activas (vigentes)
CREATE OR REPLACE VIEW active_trading_strategies AS
SELECT 
    id,
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
    executed,
    status,
    transaction_id,
    created_at,
    expires_at,
    executed_at,
    closed_at,
    EXTRACT(EPOCH FROM (expires_at - CURRENT_TIMESTAMP))/60 AS minutes_until_expiry,
    llm_response,
    market_conditions
FROM trading_strategies
WHERE status IN ('PENDING', 'OPEN') 
AND expires_at > CURRENT_TIMESTAMP
ORDER BY created_at DESC;

-- Comentarios para documentación
COMMENT ON TABLE trading_strategies IS 'Estrategias de trading generadas por el LLM con vigencia de 1 hora';
COMMENT ON COLUMN trading_strategies.action IS 'Acción de trading: SHORT o LONG';
COMMENT ON COLUMN trading_strategies.confidence IS 'Nivel de confianza del LLM (0-100%)';
COMMENT ON COLUMN trading_strategies.expires_at IS 'Timestamp de expiración (1 hora desde creación)';
COMMENT ON COLUMN trading_strategies.executed IS 'Si la estrategia fue ejecutada en Bybit';
COMMENT ON COLUMN trading_strategies.status IS 'Estado: PENDING, OPEN, CLOSED, CANCELLED, EXPIRED';
COMMENT ON COLUMN trading_strategies.transaction_id IS 'ID de transacción de Bybit (cuando se ejecute)';
COMMENT ON COLUMN trading_strategies.llm_response IS 'Respuesta completa del LLM en formato JSON';
COMMENT ON COLUMN trading_strategies.market_conditions IS 'Condiciones del mercado al momento de la estrategia';