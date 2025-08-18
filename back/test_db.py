from database.db_manager import IndicadorDB

# Prueba básica de la base de datos
print("Inicializando base de datos...")
db = IndicadorDB("test_indicadores.db")
print("Base de datos inicializada correctamente")

# Crear datos de prueba
test_data = {
    "timestamp": "2025-08-15T10:00:00",
    "symbol": "BTC/USD",
    "interval": "4h",
    "close_price": 60000,
    "rsi": 45.2,
    "sma": 59500,
    "adx": 25.0,
    "macd": 120.5,
    "macd_signal": 115.0,
    "macd_hist": 5.5,
    "bb_upper": 61000,
    "bb_middle": 60000,
    "bb_lower": 59000
}

print("Guardando datos de prueba...")
success = db.save_indicators(test_data)
print(f"Resultado: {'✅ Éxito' if success else '❌ Error'}")

print("Obteniendo datos recientes...")
recent = db.get_recent_indicators("BTC/USD", 5)
print(f"Encontrados: {len(recent)} registros")

print("Construyendo contexto para LLM...")
context = db.build_llm_context("BTC/USD", test_data)
print(f"Contexto generado: {len(context.get('recent_points', []))} puntos históricos")
print("✅ Prueba completada")
