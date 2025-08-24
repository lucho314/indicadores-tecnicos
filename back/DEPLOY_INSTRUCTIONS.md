# 📋 Instrucciones de Despliegue

## 🚀 Configuración Post-Despliegue

Después de hacer **push** y que se despliegue automáticamente, ejecuta estos comandos para asegurar que todo esté configurado correctamente:

### ✅ Opción 1: Configuración Automática (Recomendada)

```bash
# Ejecutar script de configuración post-despliegue
docker-compose run --rm app python deploy_setup.py
```

Este script:
- ✅ Verifica la conexión a PostgreSQL
- ✅ Crea automáticamente la tabla `klines` si no existe
- ✅ Sincroniza datos iniciales desde Bybit
- ✅ Verifica que todos los componentes estén funcionando
- ✅ Muestra el estado del sistema

### ✅ Opción 2: Verificación Manual

Si prefieres verificar manualmente:

```bash
# 1. Verificar que el sistema funciona
docker-compose run --rm app python main.py

# 2. Si hay problemas con la BD, ejecutar setup manual
docker-compose run --rm app python setup_new_indicators.py
```

## 🔧 Verificación Automática Integrada

El sistema ahora incluye **verificación automática** en `main.py`:

- 🔍 **Auto-detección**: Verifica automáticamente si la tabla `klines` existe
- 🛠️ **Auto-reparación**: Ejecuta la migración automáticamente si es necesario
- ⚡ **Sin interrupciones**: El sistema se configura solo en la primera ejecución

## 📊 Estado del Sistema

Para verificar el estado actual:

```bash
# Ver estado completo del sistema
docker-compose run --rm app python -c "from service.indicators_engine import IndicatorsEngine; print(IndicatorsEngine().get_system_status())"

# Verificar datos en BD
docker-compose run --rm app python view_database.py
```

## 🔄 Sincronización de Datos

El sistema sincroniza datos automáticamente:

- **Primera ejecución**: Descarga últimas 1000 velas (sincronización inicial)
- **Ejecuciones posteriores**: Solo descarga velas nuevas (sincronización incremental)
- **Ventana deslizante**: Mantiene automáticamente las últimas 1000 velas

### Sincronización Manual (si es necesario)

```bash
# Sincronización incremental
docker-compose run --rm app python -c "from service.klines_service import KlinesService; KlinesService().incremental_sync()"

# Sincronización inicial completa (solo si es necesario)
docker-compose run --rm app python -c "from service.klines_service import KlinesService; KlinesService().initial_sync()"
```

## 🎯 Flujo de Despliegue Recomendado

1. **Push al repositorio** → Despliegue automático
2. **Ejecutar configuración**: `docker-compose run --rm app python deploy_setup.py`
3. **Verificar funcionamiento**: `docker-compose run --rm app python main.py`
4. **¡Listo!** El sistema está operativo

## ⚠️ Solución de Problemas

### Error de Conexión a BD
```bash
# Verificar que PostgreSQL esté ejecutándose
docker-compose ps

# Reiniciar servicios si es necesario
docker-compose down && docker-compose up -d
```

### Tabla klines no existe
```bash
# El sistema se auto-repara, pero si hay problemas:
docker-compose run --rm app python setup_new_indicators.py
```

### Sin datos de velas
```bash
# Forzar sincronización inicial
docker-compose run --rm app python -c "from service.klines_service import KlinesService; KlinesService().initial_sync()"
```

## 📈 Indicadores Disponibles

El sistema ahora calcula y envía al LLM:

**Indicadores básicos:**
- RSI, MACD, SMA20, ADX, Bollinger Bands

**Nuevos indicadores agregados:**
- ✅ EMA20, EMA200
- ✅ SMA200
- ✅ ATR14 (volatilidad)
- ✅ OBV (volumen)
- ✅ Volumen actual

## 🔔 Notificaciones

El sistema envía alertas automáticas por:
- 📱 **WhatsApp**: Señales de trading
- 🤖 **LLM**: Análisis inteligente de posiciones

---

## 🆘 Contacto de Soporte

Si encuentras problemas:
1. Revisa los logs: `docker-compose logs app`
2. Ejecuta el diagnóstico: `docker-compose run --rm app python deploy_setup.py`
3. Verifica variables de entorno en `.env`

**¡El sistema está diseñado para ser auto-suficiente y requerir mínima intervención manual!** 🎉