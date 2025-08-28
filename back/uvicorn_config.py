#!/usr/bin/env python3
"""
Configuración optimizada para uvicorn con soporte para WebSocket y APIs REST concurrentes.

Esta configuración resuelve el problema de encolamiento de peticiones cuando se usan
WebSockets junto con APIs REST normales.
"""

import multiprocessing
import os
from typing import Dict, Any


def get_uvicorn_config() -> Dict[str, Any]:
    """
    Retorna la configuración optimizada para uvicorn.
    
    Returns:
        Diccionario con la configuración de uvicorn
    """
    # Calcular número de workers basado en CPU cores
    workers = int(os.getenv('UVICORN_WORKERS', multiprocessing.cpu_count()))
    
    # En desarrollo, usar menos workers para facilitar debugging
    if os.getenv('APP_ENV') == 'development':
        workers = min(workers, 2)
    
    config = {
        'host': '0.0.0.0',
        'port': int(os.getenv('PORT', 8000)),
        'workers': workers,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'loop': 'asyncio',
        'http': 'httptools',
        'ws': 'websockets',
        'lifespan': 'on',
        'access_log': True,
        'use_colors': True,
        'reload': os.getenv('APP_ENV') == 'development',
        'reload_dirs': ['./api', './service'] if os.getenv('APP_ENV') == 'development' else None,
        # Configuraciones de timeout para evitar bloqueos
        'timeout_keep_alive': 5,
        'timeout_notify': 30,
        'timeout_graceful_shutdown': 30,
        # Configuraciones de límites
        'limit_concurrency': 1000,
        'limit_max_requests': 10000,
        'backlog': 2048,
    }
    
    return config


def run_server():
    """
    Ejecuta el servidor con la configuración optimizada.
    """
    import uvicorn
    from api.main import app
    
    config = get_uvicorn_config()
    
    print(f"🚀 Iniciando servidor con {config['workers']} workers")
    print(f"🔧 Configuración: {config}")
    
    uvicorn.run(app, **config)


if __name__ == '__main__':
    run_server()