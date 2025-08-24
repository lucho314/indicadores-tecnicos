#!/usr/bin/env python3
"""
Script para expirar automáticamente estrategias de trading vencidas.
Este script debe ejecutarse periódicamente (cada 5-10 minutos) mediante cron o tarea programada.

Uso:
    python expire_strategies.py [--verbose] [--dry-run]
    
Opciones:
    --verbose: Mostrar información detallada
    --dry-run: Solo mostrar qué estrategias se expirarían sin hacer cambios
"""

import sys
import os
import argparse
import logging
from datetime import datetime
from typing import Dict, Any

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_indicador_db import PostgresIndicadorDB
from service.trading_strategy_service import TradingStrategyService

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configura el logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('expire_strategies.log', encoding='utf-8')
        ]
    )
    
    return logging.getLogger(__name__)

def expire_strategies(dry_run: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """Expira estrategias vencidas
    
    Args:
        dry_run: Si es True, solo muestra qué se haría sin hacer cambios
        verbose: Si es True, muestra información detallada
        
    Returns:
        Diccionario con el resultado de la operación
    """
    logger = setup_logging(verbose)
    
    try:
        logger.info("Iniciando proceso de expiración de estrategias")
        
        # Inicializar servicios
        db = PostgresIndicadorDB()
        strategy_service = TradingStrategyService(db)
        
        # Obtener estrategias que van a expirar
        if dry_run or verbose:
            logger.info("Consultando estrategias que van a expirar...")
            
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, symbol, action, confidence, entry_price, 
                               created_at, expires_at, status,
                               EXTRACT(EPOCH FROM (expires_at - CURRENT_TIMESTAMP))/60 AS minutes_until_expiry
                        FROM trading_strategies 
                        WHERE status IN ('PENDING', 'OPEN') 
                        AND expires_at < CURRENT_TIMESTAMP
                        ORDER BY expires_at ASC
                    """)
                    
                    expired_strategies = cur.fetchall()
                    
                    if expired_strategies:
                        logger.info(f"Encontradas {len(expired_strategies)} estrategias para expirar:")
                        
                        for strategy in expired_strategies:
                            strategy_id, symbol, action, confidence, entry_price, created_at, expires_at, status, minutes_overdue = strategy
                            logger.info(
                                f"  ID {strategy_id}: {action} {symbol} @ ${entry_price} "
                                f"(Confianza: {confidence}%, Estado: {status}, "
                                f"Vencida hace {abs(minutes_overdue):.1f} min)"
                            )
                    else:
                        logger.info("No hay estrategias para expirar")
        
        # Ejecutar expiración si no es dry-run
        if not dry_run:
            expired_count = strategy_service.expire_old_strategies()
            logger.info(f"Expiradas {expired_count} estrategias")
        else:
            expired_count = len(expired_strategies) if 'expired_strategies' in locals() else 0
            logger.info(f"DRY RUN: Se expirarían {expired_count} estrategias")
        
        # Obtener estadísticas actuales
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COUNT(CASE WHEN status = 'PENDING' THEN 1 END) as pending,
                        COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open,
                        COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed,
                        COUNT(CASE WHEN status = 'EXPIRED' THEN 1 END) as expired,
                        COUNT(CASE WHEN status = 'CANCELLED' THEN 1 END) as cancelled
                    FROM trading_strategies 
                    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                """)
                
                stats = cur.fetchone()
                pending, open_count, closed, expired_total, cancelled = stats
                
                logger.info(f"Estadísticas últimas 24h: {pending} pendientes, {open_count} abiertas, "
                           f"{closed} cerradas, {expired_total} expiradas, {cancelled} canceladas")
        
        result = {
            "success": True,
            "expired_count": expired_count,
            "dry_run": dry_run,
            "timestamp": datetime.now().isoformat(),
            "stats_24h": {
                "pending": pending,
                "open": open_count,
                "closed": closed,
                "expired": expired_total,
                "cancelled": cancelled
            }
        }
        
        logger.info("Proceso de expiración completado exitosamente")
        return result
        
    except Exception as e:
        logger.error(f"Error en proceso de expiración: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Expira estrategias de trading vencidas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python expire_strategies.py                    # Expirar estrategias normalmente
  python expire_strategies.py --verbose          # Mostrar información detallada
  python expire_strategies.py --dry-run          # Solo mostrar qué se haría
  python expire_strategies.py --dry-run --verbose # Modo detallado sin cambios

Este script debe ejecutarse periódicamente (cada 5-10 minutos) para
mantener las estrategias actualizadas.
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Solo mostrar qué estrategias se expirarían sin hacer cambios'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Salida en formato JSON'
    )
    
    args = parser.parse_args()
    
    # Ejecutar expiración
    result = expire_strategies(dry_run=args.dry_run, verbose=args.verbose)
    
    # Mostrar resultado
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            action = "se expirarían" if result['dry_run'] else "expiradas"
            print(f"✅ Proceso completado: {result['expired_count']} estrategias {action}")
        else:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)

if __name__ == '__main__':
    main()