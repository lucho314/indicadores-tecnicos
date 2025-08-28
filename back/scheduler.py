import time
import schedule
import subprocess
import logging
import os
from datetime import datetime
from database.postgres_db_manager import PostgresIndicadorDB

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CryptoScheduler:
    def __init__(self):
        self.db = PostgresIndicadorDB()
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
    def run_analysis(self, symbol: str):
        """Ejecutar análisis para un símbolo específico"""
        start_time = time.time()
        
        try:
            logger.info(f"🚀 Iniciando análisis para {symbol}")
            
            # Ejecutar el script principal
            result = subprocess.run(
                ['python', 'main.py', '--symbol', symbol, '--json'],
                capture_output=True,
                text=True,
                timeout=20  # 20 segundos timeout
            )
            
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"✅ {symbol} completado exitosamente en {execution_time:.2f}s")
                
                # Registrar éxito en BD
                self.db.log_execution(
                    symbol=symbol,
                    status='success',
                    message=f'Análisis completado en {execution_time:.2f}s',
                    execution_time=execution_time
                )
                
                # Log del output
                if result.stdout:
                    logger.info(f"Output {symbol}: {result.stdout[:200]}...")
                    
            else:
                error_msg = f"Error en {symbol}: {result.stderr}"
                logger.error(error_msg)
                
                # Registrar error en BD
                self.db.log_execution(
                    symbol=symbol,
                    status='error',
                    message=f'Falló en {execution_time:.2f}s',
                    execution_time=execution_time,
                    error_details=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            error_msg = f"Timeout en {symbol} después de {execution_time:.2f}s"
            logger.error(error_msg)
            
            self.db.log_execution(
                symbol=symbol,
                status='timeout',
                message=error_msg,
                execution_time=execution_time,
                error_details='Proceso excedió el tiempo límite de 5 minutos'
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Excepción en {symbol}: {str(e)}"
            logger.error(error_msg)
            
            self.db.log_execution(
                symbol=symbol,
                status='exception',
                message=error_msg,
                execution_time=execution_time,
                error_details=str(e)
            )
    
    def run_full_analysis(self):
        """Ejecutar análisis completo de todos los símbolos"""
        logger.info("🎯 ===== INICIANDO CICLO COMPLETO =====")
        
        for i, symbol in enumerate(self.symbols):
            self.run_analysis(symbol)
            
            # Esperar entre símbolos para respetar rate limits
            if i < len(self.symbols) - 1:  # No esperar después del último
                logger.info("⏳ Esperando 150 segundos entre símbolos...")
                time.sleep(150)
        
        # Limpiar datos antiguos ocasionalmente
        current_hour = datetime.now().hour
        if current_hour == 0:  # Una vez al día a medianoche
            logger.info("🧹 Ejecutando limpieza de datos antiguos...")
            self.db.cleanup_old_data(30)
        
        logger.info("✅ ===== CICLO COMPLETO TERMINADO =====")
        
        # Mostrar estadísticas
        stats = self.db.get_execution_stats(24)
        if stats:
            logger.info(f"📊 Últimas 24h: {stats.get('total_executions', 0)} ejecuciones, "
                       f"{stats.get('successful', 0)} éxitos, {stats.get('errors', 0)} errores")

def main():
    """Función principal del scheduler"""
    logger.info("🚀 Iniciando Crypto Indicators Scheduler")
    
    # Verificar variables de entorno
    required_vars = ['TWELVEDATA_API_KEY', 'OPENAI_API_KEY', 'WHATSAPP_PHONE', 'WHATSAPP_APIKEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.warning(f"⚠️  Variables de entorno faltantes: {', '.join(missing_vars)}")
    else:
        logger.info("✅ Todas las variables de entorno están configuradas")
    
    scheduler = CryptoScheduler()
    
    # Programar ejecución cada 4 horas
    schedule.every(4).hours.do(scheduler.run_full_analysis)
    
    # Ejecutar una vez al inicio (opcional)
    if os.getenv('RUN_ON_START', 'true').lower() == 'true':
        logger.info("🏃‍♂️ Ejecutando análisis inicial...")
        scheduler.run_full_analysis()
    
    logger.info("⏰ Scheduler configurado para ejecutar cada 4 horas")
    logger.info("🔄 Esperando próxima ejecución...")
    
    # Loop principal
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            logger.info("👋 Scheduler detenido por el usuario")
            break
        except Exception as e:
            logger.error(f"❌ Error en scheduler: {e}")
            time.sleep(60)  # Esperar antes de reintentar

if __name__ == "__main__":
    main()
