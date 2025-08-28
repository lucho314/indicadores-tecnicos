# Optimización de WebSocket y Concurrencia

## Problema Identificado

El servidor uvicorn estaba experimentando problemas de encolamiento de peticiones donde:

1. **WebSocket bloqueante**: Las conexiones WebSocket realizaban llamadas síncronas a la API de Bybit cada 5 segundos
2. **Event loop bloqueado**: Estas llamadas bloqueantes impedían que otras peticiones REST se procesaran
3. **Configuración subóptima**: uvicorn ejecutándose con un solo worker sin optimizaciones de concurrencia

## Soluciones Implementadas

### 1. Configuración Optimizada de Uvicorn

**Archivo**: `uvicorn_config.py`

- **Workers múltiples**: Configuración automática basada en CPU cores
- **Worker class**: `uvicorn.workers.UvicornWorker` para mejor manejo de WebSockets
- **Timeouts configurados**: Evita conexiones colgadas
- **Límites de concurrencia**: Control de carga del servidor

```python
config = {
    'workers': multiprocessing.cpu_count(),
    'worker_class': 'uvicorn.workers.UvicornWorker',
    'timeout_keep_alive': 5,
    'limit_concurrency': 1000,
    'backlog': 2048,
}
```

### 2. WebSocket Asíncrono No Bloqueante

**Archivo**: `api/main.py` - función `websocket_positions`

**Antes** (bloqueante):
```python
# Llamadas síncronas que bloquean el event loop
position = bybit_service.get_open_position(symbol)
balance = bybit_service.get_available_balance()
current_price = bybit_service.get_price(symbol)
```

**Después** (no bloqueante):
```python
# Ejecutar en thread pool para no bloquear el event loop
loop = asyncio.get_event_loop()
position_task = loop.run_in_executor(None, bybit_service.get_open_position, symbol)
balance_task = loop.run_in_executor(None, bybit_service.get_available_balance)
price_task = loop.run_in_executor(None, bybit_service.get_price, symbol)

# Ejecutar en paralelo con timeout
position, balance, current_price = await asyncio.wait_for(
    asyncio.gather(position_task, balance_task, price_task),
    timeout=10.0
)
```

### 3. Scripts de Ejecución Optimizados

**Archivo**: `run_optimized.ps1`

- Script PowerShell para diferentes entornos
- Configuración automática de workers
- Soporte para desarrollo y producción

## Beneficios de las Optimizaciones

### ✅ Concurrencia Mejorada
- Las peticiones REST ya no se bloquean por WebSockets activos
- Múltiples conexiones WebSocket pueden funcionar simultáneamente
- Mejor utilización de recursos del servidor

### ✅ Rendimiento
- Llamadas paralelas a la API de Bybit (position, balance, price)
- Timeouts configurados evitan conexiones colgadas
- Workers múltiples distribuyen la carga

### ✅ Estabilidad
- Manejo de errores mejorado con timeouts
- Recuperación automática de conexiones fallidas
- Logs detallados para debugging

### ✅ Escalabilidad
- Configuración automática basada en hardware disponible
- Límites de concurrencia configurables
- Soporte para entornos de desarrollo y producción

## Uso

### Desarrollo
```bash
# PowerShell
.\run_optimized.ps1 -Environment development

# O directamente
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --reload
```

### Producción
```bash
# PowerShell
.\run_optimized.ps1 -Environment production

# O usando la configuración optimizada
python uvicorn_config.py

# Docker
docker-compose up api
```

## Monitoreo

Para verificar que las optimizaciones funcionan:

1. **Conectar WebSocket**: Abrir conexión a `/ws/positions/BTCUSDT`
2. **Probar API REST**: Hacer peticiones a `/indicators/BTCUSDT` simultáneamente
3. **Verificar logs**: Los logs deben mostrar procesamiento concurrente
4. **Medir latencia**: Las peticiones REST no deben tener latencia adicional

## Configuración de Variables de Entorno

```bash
# Número de workers (opcional, se calcula automáticamente)
UVICORN_WORKERS=4

# Entorno de ejecución
APP_ENV=production  # o development

# Puerto del servidor
PORT=8000
```

## Troubleshooting

### Problema: WebSocket se desconecta frecuentemente
**Solución**: Verificar que `timeout_keep_alive` esté configurado apropiadamente

### Problema: APIs REST siguen lentas
**Solución**: Verificar que se esté usando `uvicorn.workers.UvicornWorker` y múltiples workers

### Problema: Alto uso de CPU
**Solución**: Ajustar el número de workers o aumentar el intervalo de actualización del WebSocket

### Problema: Errores de timeout en Bybit
**Solución**: Aumentar el timeout en `asyncio.wait_for()` o verificar conectividad de red