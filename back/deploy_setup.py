#!/usr/bin/env python3
"""
Script de configuración post-despliegue
Ejecuta este script después de hacer push para asegurar que la base de datos esté lista
"""

import sys
import os
from datetime import datetime
from database.postgres_db_manager import PostgresIndicadorDB
from service.klines_service import KlinesService
from service.indicators_engine import IndicatorsEngine

def main():
    """
    Configuración completa post-despliegue
    """
    print("🚀 Iniciando configuración post-despliegue...")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    try:
        # 1. Verificar conexión a base de datos
        print("\n1️⃣ Verificando conexión a PostgreSQL...")
        db_manager = PostgresIndicadorDB()
        print("✅ Conexión a PostgreSQL exitosa")
        
        # 2. Ejecutar migración de tabla klines
        print("\n2️⃣ Verificando y creando tabla 'klines'...")
        script_path = os.path.join(os.path.dirname(__file__), "database", "create_klines_table.sql")
        
        if not os.path.exists(script_path):
            print(f"❌ Script de migración no encontrado: {script_path}")
            return False
            
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_script)
                conn.commit()
                
        print("✅ Tabla 'klines' configurada exitosamente")
        
        # 2.1. Ejecutar migración de tabla trading_strategies
        print("\n2️⃣.1️⃣ Verificando y creando tabla 'trading_strategies'...")
        script_path = os.path.join(os.path.dirname(__file__), "database", "create_trading_strategies_table.sql")
        
        if not os.path.exists(script_path):
            print(f"❌ Script de migración no encontrado: {script_path}")
            return False
            
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_script)
                conn.commit()
                
        print("✅ Tabla 'trading_strategies' configurada exitosamente")
        
        # 3. Verificar tablas existentes
        print("\n3️⃣ Verificando tablas en base de datos...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                tables = [row[0] for row in cur.fetchall()]
                
        print(f"📊 Tablas disponibles: {', '.join(tables)}")
        
        # 4. Sincronización inicial de datos (opcional)
        print("\n4️⃣ Iniciando sincronización inicial de datos...")
        try:
            klines_service = KlinesService(db_manager)
            
            # Verificar si ya hay datos
            latest_time = klines_service.get_latest_kline_time("BTCUSDT", "240")
            
            if latest_time:
                print(f"📈 Datos existentes encontrados. Última vela: {datetime.fromtimestamp(latest_time/1000)}")
                print("🔄 Ejecutando sincronización incremental...")
                saved_count = klines_service.incremental_sync("BTCUSDT", "240")
            else:
                print("📥 No hay datos previos. Ejecutando sincronización inicial...")
                saved_count = klines_service.initial_sync("BTCUSDT", "240")
                
            print(f"✅ Sincronización completada: {saved_count} velas procesadas")
            
        except Exception as e:
            print(f"⚠️ Error en sincronización (no crítico): {e}")
            print("💡 La sincronización se ejecutará automáticamente en el próximo análisis")
        
        # 5. Verificar motor de indicadores
        print("\n5️⃣ Verificando motor de indicadores...")
        try:
            engine = IndicatorsEngine(db_manager)
            status = engine.get_system_status("BTCUSDT", "240")
            
            print(f"📊 Estado del sistema:")
            print(f"   - Velas en BD: {status.get('klines_count', 0)}")
            print(f"   - Última vela: {status.get('latest_kline_time', 'N/A')}")
            print(f"   - Sistema inicializado: {status.get('system_initialized', False)}")
            
        except Exception as e:
            print(f"⚠️ Error verificando motor de indicadores: {e}")
        
        print("\n" + "="*60)
        print("🎉 CONFIGURACIÓN POST-DESPLIEGUE COMPLETADA EXITOSAMENTE")
        print("\n📋 Próximos pasos:")
        print("   1. El sistema está listo para ejecutar análisis")
        print("   2. Ejecuta 'python main.py' para probar el análisis completo")
        print("   3. Los datos se sincronizarán automáticamente en cada ejecución")
        print("\n🔧 Comandos útiles:")
        print("   - Análisis manual: python main.py")
        print("   - Verificar estado: python -c \"from service.indicators_engine import IndicatorsEngine; print(IndicatorsEngine().get_system_status())\"")
        print("   - Sincronizar datos: python -c \"from service.klines_service import KlinesService; KlinesService().incremental_sync()\"")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN CONFIGURACIÓN: {e}")
        print("\n🔧 Soluciones sugeridas:")
        print("   1. Verificar que PostgreSQL esté ejecutándose")
        print("   2. Verificar variables de entorno de base de datos")
        print("   3. Ejecutar manualmente: python setup_new_indicators.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)