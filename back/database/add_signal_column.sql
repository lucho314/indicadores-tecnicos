-- Agregar columna signal a la tabla indicadores
-- Este campo indica si hay una señal activa (LLM respondió con acción != 'WAIT')

ALTER TABLE indicadores 
ADD COLUMN IF NOT EXISTS signal BOOLEAN DEFAULT FALSE;

-- Crear índice para mejorar performance en consultas de señales
CREATE INDEX IF NOT EXISTS idx_indicadores_signal 
ON indicadores(signal) 
WHERE signal = TRUE;

-- Crear índice compuesto para búsquedas por símbolo y señal
CREATE INDEX IF NOT EXISTS idx_indicadores_symbol_signal 
ON indicadores(symbol, signal, timestamp DESC);

-- Comentario para documentación
COMMENT ON COLUMN indicadores.signal IS 'Indica si hay una señal activa de trading (TRUE cuando LLM responde con acción diferente a WAIT)';
