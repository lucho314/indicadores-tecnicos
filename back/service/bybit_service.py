from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_API_SECRET,APP_ENV
import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class BybitService:
    def __init__(self):
        print("🔧 Inicializando BybitService...")
        
        # Debug: verificar las credenciales
        api_key = BYBIT_API_KEY or os.getenv('BYBIT_API_KEY')
        api_secret = BYBIT_API_SECRET or os.getenv('BYBIT_API_SECRET')
        
        logger.info(f"🔍 Verificando credenciales de Bybit...${api_key}"  )
        # mostrar las credenciales (parcialmente para seguridad)
        print(f"🔑 API Key: {api_key[:10]}..." if api_key else "❌ API Key no encontrada")
        print(f"🔐 API Secret: {api_secret[:10]}..." if api_secret else "❌ API Secret no encontrada")
        
        if not api_key or not api_secret:
            raise Exception("❌ Credenciales de Bybit no configuradas")
        
        # Configurar cliente con timeout para testnet
        print(f"🌐 Configurando cliente para Bybit Testnetttt...{APP_ENV}")
        self.client = HTTP(
            api_key=api_key,
            api_secret=api_secret,
            timeout=10,    # Timeout de 10 segundos
            recv_window=5000,  # Ventana de recepción más amplia
            testnet=True if APP_ENV == 'development' else False  # Usar testnet en desarrollo
        )
        
        # Verificar que esté usando testnet
        print(f"🔗 Cliente configurado para: {'Testnet' if self.client.testnet else 'Mainnet'}")
        print(f"📡 Base URL: {getattr(self.client, 'endpoint', 'No disponible')}")
        print("✅ BybitService inicializado correctamente")

    def test_connection(self):
        """
        Prueba la conexión con Bybit testnet
        """
        try:
            print("🧪 Probando conexión con Bybit...")
            
            # Obtener información del servidor
            response = self.client.get_server_time()
            print(f"⏰ Tiempo del servidor: {response}")
            
            # Intentar obtener información de la cuenta (sin coin específico)
            account_response = self.client.get_wallet_balance(accountType="UNIFIED")
            print(f"💼 Respuesta de cuenta: {account_response}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en prueba de conexión: {str(e)}")
            return False

    def get_open_position(self, symbol: str):
        """
        Obtiene la posición abierta para un símbolo específico
        
        Args:
            symbol: Símbolo del par (ej: 'BTCUSDT')
            
        Returns:
            Diccionario con la posición abierta o None si no hay posición
        """
        try:
            print(f"📊 Consultando posición para {symbol}...")
            
            response = self.client.get_positions(
                category="linear",
                symbol=symbol
            )
            
            print(f"📋 Respuesta raw para {symbol}: {type(response)} - {response}")
            
            # La respuesta de pybit puede ser una tupla o diccionario
            # Extraer el contenido real de la respuesta
            if isinstance(response, tuple):
                data = response[0]  # El primer elemento suele ser la data
                print(f"📦 Datos extraídos de tupla: {data}")
            else:
                data = response
                print(f"📦 Datos directos: {data}")
            
            # Buscar la posición abierta (size > 0)
            if data and isinstance(data, dict):
                result = data.get('result', {})
                positions = result.get('list', [])
                print(f"📋 Posiciones encontradas para {symbol}: {len(positions)}")
                
                for position in positions:
                    size = float(position.get('size', 0))
                    if size != 0:
                        print(f"✅ Posición activa para {symbol}: size={size}")
                        return position
                
                print(f"ℹ️ No hay posiciones activas para {symbol}")
            else:
                print(f"⚠️ Formato de respuesta inesperado para {symbol}: {data}")
            
            return None
            
        except Exception as e:
            print(f"💥 Error consultando posición para {symbol}: {str(e)}")
            raise Exception(f"Error consultando posición abierta: {str(e)}")

    def get_available_balance(self):
        """
        Obtiene el balance disponible para invertir
        
        Returns:
            Diccionario con información del balance disponible
        """
        try:
            print("💰 Consultando balance de la cuenta...")
            
            response = self.client.get_wallet_balance(
                accountType="UNIFIED",
                coin="USDT"
            )
            
            print(f"💼 Respuesta balance raw: {type(response)} - {response}")
            
            # La respuesta de pybit puede ser una tupla o diccionario
            if isinstance(response, tuple):
                data = response[0]
                print(f"💼 Datos balance de tupla: {data}")
            else:
                data = response
                print(f"💼 Datos balance directos: {data}")
            
            if data and isinstance(data, dict):
                result = data.get('result', {})
                coin_list = result.get('list', [])
                print(f"💰 Cuentas encontradas: {len(coin_list)}")
                
                if coin_list:
                    account_info = coin_list[0]
                    coins = account_info.get('coin', [])
                    print(f"🪙 Monedas en cuenta: {len(coins)}")
                    
                    for coin in coins:
                        if coin.get('coin') == 'USDT':
                            # Función helper para convertir strings vacíos a 0
                            def safe_float(value, default=0):
                                try:
                                    return float(value) if value != '' else default
                                except (ValueError, TypeError):
                                    return default
                            
                            balance_info = {
                                'coin': coin.get('coin'),
                                'walletBalance': safe_float(coin.get('walletBalance', 0)),
                                'availableToWithdraw': safe_float(coin.get('availableToWithdraw', 0)),
                                'transferBalance': safe_float(coin.get('totalAvailableBalance', 0)),  # Usar totalAvailableBalance
                                'bonus': safe_float(coin.get('bonus', 0)),
                                'equity': safe_float(coin.get('equity', 0)),
                                'usdValue': safe_float(coin.get('usdValue', 0))
                            }
                            print(f"✅ Balance USDT encontrado: {balance_info}")
                            return balance_info
            
            print("⚠️ No se encontró balance USDT, devolviendo balance vacío")
            return {
                'coin': 'USDT',
                'walletBalance': 0,
                'availableToWithdraw': 0,
                'transferBalance': 0,
                'bonus': 0
            }
            
        except Exception as e:
            print(f"💥 Error consultando balance: {str(e)}")
            raise Exception(f"Error consultando balance disponible: {str(e)}")
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Obtiene el precio actual de un par de trading.

        Args:
            symbol: Símbolo del par (ej: 'BTCUSDT')

        Returns:
            El precio actual como float, o None si ocurre un error.
        """
        try:
            print(f"💹 Consultando precio para {symbol}...")
            
            # Llamada a la API de Bybit para obtener el precio
            response = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )
            
            print(f"📋 Respuesta raw para {symbol}: {type(response)} - {response}")
            
            # Extraer el precio del resultado
            if isinstance(response, dict) and response.get('retCode') == 0:
                result = response.get('result', {})
                ticker_list = result.get('list', [])
                
                # Validar que la lista de tickers no esté vacía
                if ticker_list and isinstance(ticker_list, list):
                    ticker = ticker_list[0]  # Tomar el primer resultado
                    last_price = ticker.get('lastPrice')
                    
                    if last_price:
                        price = float(last_price)
                        print(f"✅ Precio actual para {symbol}: {price}")
                        return price
            
            print(f"⚠️ No se pudo obtener el precio para {symbol}")
            return None
        
        except Exception as e:
            print(f"💥 Error consultando precio para {symbol}: {str(e)}")
            raise Exception(f"Error consultando precio: {str(e)}")

