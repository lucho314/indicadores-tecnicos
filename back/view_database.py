import sqlite3
import json
from datetime import datetime
from database.db_manager import IndicadorDB

def view_database():
    """Explorar y visualizar datos de la base de datos"""
    
    print("🗄️ EXPLORADOR DE BASE DE DATOS")
    print("="*60)
    
    try:
        db = IndicadorDB()
        
        # 1. Información general de la base de datos
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Contar total de registros
            cursor.execute("SELECT COUNT(*) FROM indicadores")
            total_records = cursor.fetchone()[0]
            
            # Símbolos únicos
            cursor.execute("SELECT DISTINCT symbol FROM indicadores")
            symbols = [row[0] for row in cursor.fetchall()]
            
            # Rango de fechas
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM indicadores")
            date_range = cursor.fetchone()
            
            print("📊 RESUMEN GENERAL:")
            print(f"Total de registros: {total_records}")
            print(f"Símbolos: {', '.join(symbols) if symbols else 'Ninguno'}")
            print(f"Rango de fechas: {date_range[0]} → {date_range[1]}")
            print()
        
        # 2. Mostrar últimos registros
        print("📈 ÚLTIMOS 10 REGISTROS:")
        print("-" * 60)
        
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Para acceso por nombre de columna
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM indicadores 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            
            records = cursor.fetchall()
            
            if not records:
                print("❌ No hay datos en la base de datos")
                return
            
            for i, record in enumerate(records, 1):
                print(f"🔸 Registro #{i}")
                print(f"   📅 Fecha: {record['created_at']}")
                print(f"   📊 Símbolo: {record['symbol']} ({record['interval_tf']})")
                print(f"   💰 Precio: ${record['close_price']}")
                print(f"   📈 RSI: {record['rsi']}")
                print(f"   📉 MACD_Hist: {record['macd_hist']}")
                print(f"   📊 SMA: {record['sma']}")
                print(f"   📶 ADX: {record['adx']}")
                print()
        
        # 3. Estadísticas por símbolo
        print("📊 ESTADÍSTICAS POR SÍMBOLO:")
        print("-" * 60)
        
        for symbol in symbols:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        COUNT(*) as count,
                        MIN(rsi) as rsi_min,
                        MAX(rsi) as rsi_max,
                        AVG(rsi) as rsi_avg,
                        MIN(macd_hist) as macd_min,
                        MAX(macd_hist) as macd_max,
                        AVG(macd_hist) as macd_avg
                    FROM indicadores 
                    WHERE symbol = ? AND rsi IS NOT NULL
                """, (symbol,))
                
                stats = cursor.fetchone()
                
                if stats and stats[0] > 0:
                    print(f"🎯 {symbol}:")
                    print(f"   📝 Registros: {stats[0]}")
                    print(f"   📈 RSI: {stats[1]:.1f} - {stats[2]:.1f} (avg: {stats[3]:.1f})")
                    print(f"   📉 MACD_Hist: {stats[4]:.2f} - {stats[5]:.2f} (avg: {stats[6]:.2f})")
                    print()
        
        # 4. Buscar oportunidades históricas
        print("🎯 OPORTUNIDADES HISTÓRICAS (RSI < 30 o MACD_Hist > 0):")
        print("-" * 60)
        
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT symbol, created_at, rsi, macd_hist, close_price
                FROM indicadores 
                WHERE (rsi < 30 OR macd_hist > 0) 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            opportunities = cursor.fetchall()
            
            if opportunities:
                for opp in opportunities:
                    rsi_signal = "🟢" if opp['rsi'] and opp['rsi'] < 30 else ""
                    macd_signal = "🟢" if opp['macd_hist'] and opp['macd_hist'] > 0 else ""
                    
                    print(f"⚡ {opp['symbol']} - {opp['created_at']} {rsi_signal}{macd_signal}")
                    print(f"   RSI: {opp['rsi']:.1f} | MACD_Hist: {opp['macd_hist']:.2f} | Precio: ${opp['close_price']}")
            else:
                print("❌ No se encontraron oportunidades históricas")
        
        # 5. Opción interactiva
        print("\n" + "="*60)
        print("🔍 OPCIONES ADICIONALES:")
        print("1. Ver registro específico por ID")
        print("2. Buscar por símbolo")
        print("3. Ver datos crudos (JSON)")
        print("4. Salir")
        
        while True:
            try:
                choice = input("\nSelecciona una opción (1-4): ").strip()
                
                if choice == "1":
                    record_id = input("Ingresa el ID del registro: ").strip()
                    show_specific_record(db, record_id)
                    
                elif choice == "2":
                    symbol = input("Ingresa el símbolo (ej: BTC/USD): ").strip()
                    show_symbol_data(db, symbol)
                    
                elif choice == "3":
                    show_raw_data(db)
                    
                elif choice == "4":
                    print("👋 ¡Hasta luego!")
                    break
                    
                else:
                    print("❌ Opción inválida")
                    
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
                
    except Exception as e:
        print(f"❌ Error explorando la base de datos: {e}")

def show_specific_record(db, record_id):
    """Mostrar un registro específico"""
    try:
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM indicadores WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            
            if record:
                print(f"\n📋 REGISTRO #{record_id}:")
                print("-" * 40)
                for key in record.keys():
                    value = record[key]
                    if key == 'raw_data' and value:
                        try:
                            parsed = json.loads(value)
                            print(f"{key}: {json.dumps(parsed, indent=2)}")
                        except:
                            print(f"{key}: {value}")
                    else:
                        print(f"{key}: {value}")
            else:
                print(f"❌ No se encontró registro con ID {record_id}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def show_symbol_data(db, symbol):
    """Mostrar datos de un símbolo específico"""
    try:
        recent = db.get_recent_indicators(symbol, 5)
        
        if recent:
            print(f"\n📊 ÚLTIMOS 5 REGISTROS DE {symbol}:")
            print("-" * 50)
            
            for record in recent:
                print(f"📅 {record['created_at']}")
                print(f"   RSI: {record['rsi']} | MACD_Hist: {record['macd_hist']}")
                print(f"   Precio: ${record['close_price']} | SMA: {record['sma']}")
                print()
        else:
            print(f"❌ No se encontraron datos para {symbol}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def show_raw_data(db):
    """Mostrar algunos datos crudos"""
    try:
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, symbol, raw_data 
                FROM indicadores 
                WHERE raw_data IS NOT NULL 
                ORDER BY created_at DESC 
                LIMIT 3
            """)
            
            records = cursor.fetchall()
            
            if records:
                print(f"\n🔍 ÚLTIMOS 3 DATOS CRUDOS (JSON):")
                print("-" * 60)
                
                for record in records:
                    print(f"📋 ID {record['id']} - {record['symbol']}:")
                    try:
                        raw_data = json.loads(record['raw_data'])
                        print(json.dumps(raw_data, indent=2))
                    except:
                        print(record['raw_data'])
                    print("-" * 40)
            else:
                print("❌ No hay datos crudos disponibles")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    view_database()
