from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY, BYBIT_API_SECRET,APP_ENV
import os
import logging
import time
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
            timeout=15,    # Timeout aumentado a 15 segundos
            recv_window=30000,  # Ventana de recepción ampliada para evitar errores de timestamp
            testnet=True if APP_ENV == 'development' else False  # Usar testnet en desarrollo
        )
        
        # Sincronizar tiempo con el servidor
        self._sync_server_time()
        
        # Verificar que esté usando testnet
        print(f"🔗 Cliente configurado para: {'Testnet' if self.client.testnet else 'Mainnet'}")
        print(f"📡 Base URL: {getattr(self.client, 'endpoint', 'No disponible')}")
        print("✅ BybitService inicializado correctamente")

    def _sync_server_time(self):
        """
        Sincroniza el tiempo local con el servidor de Bybit para evitar errores de timestamp
        """
        try:
            print("⏰ Sincronizando tiempo con servidor Bybit...")
            
            # Obtener tiempo del servidor
            server_time_response = self.client.get_server_time()
            
            if isinstance(server_time_response, dict) and server_time_response.get('retCode') == 0:
                server_time_ms = int(server_time_response['result']['timeSecond']) * 1000
                local_time_ms = int(time.time() * 1000)
                
                time_diff = server_time_ms - local_time_ms
                
                print(f"🕐 Tiempo servidor: {server_time_ms}")
                print(f"🕐 Tiempo local: {local_time_ms}")
                print(f"⏱️ Diferencia: {time_diff}ms")
                
                # Si la diferencia es mayor a 1 segundo, ajustar recv_window
                if abs(time_diff) > 1000:
                    new_recv_window = 30000 + abs(time_diff) + 5000  # Agregar buffer adicional
                    print(f"⚠️ Gran diferencia de tiempo detectada. Ajustando recv_window a {new_recv_window}ms")
                    
                    # Recrear cliente con recv_window ajustado
                    api_key = BYBIT_API_KEY or os.getenv('BYBIT_API_KEY')
                    api_secret = BYBIT_API_SECRET or os.getenv('BYBIT_API_SECRET')
                    
                    self.client = HTTP(
                        api_key=api_key,
                        api_secret=api_secret,
                        timeout=15,
                        recv_window=int(new_recv_window),
                        testnet=True if APP_ENV == 'development' else False
                    )
                    
                    print(f"✅ Cliente recreado con recv_window: {new_recv_window}ms")
                else:
                    print("✅ Sincronización de tiempo correcta")
            else:
                print(f"⚠️ No se pudo obtener tiempo del servidor: {server_time_response}")
                
        except Exception as e:
            print(f"⚠️ Error sincronizando tiempo: {str(e)}")
            print("🔄 Continuando con configuración por defecto...")

    def _execute_with_retry(self, func, *args, max_retries=2, **kwargs):
        """
        Ejecuta una función de la API con reintentos automáticos y sincronización de tiempo
        
        Args:
            func: Función de la API a ejecutar
            *args: Argumentos posicionales para la función
            max_retries: Número máximo de reintentos
            **kwargs: Argumentos con nombre para la función
            
        Returns:
            Resultado de la función de la API
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                error_str = str(e)
                last_exception = e
                
                # Verificar si es un error de timestamp o retries exceeded
                is_timestamp_error = (
                    "timestamp" in error_str.lower() or 
                    "recv_window" in error_str.lower() or 
                    "10002" in error_str or
                    "retries exceeded maximum" in error_str.lower()
                )
                
                if is_timestamp_error:
                    if attempt < max_retries:
                        print(f"⚠️ Error de timestamp/retries detectado (intento {attempt + 1}/{max_retries + 1}): {error_str[:100]}...")
                        print("🔄 Resincronizando tiempo con servidor...")
                        
                        # Resincronizar tiempo y reconfigurar cliente
                        self._sync_server_time()
                        
                        # Esperar un poco más antes del siguiente intento
                        time.sleep(2)
                        continue
                    else:
                        print(f"❌ Error de timestamp persistente después de {max_retries} reintentos")
                        raise e
                else:
                    # Si no es un error de timestamp, no reintentar
                    raise e
        
        # Si llegamos aquí, todos los reintentos fallaron
        raise last_exception
    
    def _cancel_existing_orders(self, symbol: str, base_order_link_id: str):
        """
        Cancela órdenes existentes que coincidan con el patrón base del orderLinkId
        para evitar errores de duplicados.
        
        Args:
            symbol: Símbolo del par
            base_order_link_id: Patrón base del orderLinkId (ej: STRATEGY_5_ETHUSDT_Sell)
        """
        try:
            print(f"🔍 Verificando órdenes existentes para {base_order_link_id}...")
            
            # Obtener órdenes abiertas
            open_orders_response = self._execute_with_retry(
                self.client.get_open_orders,
                category="linear",
                symbol=symbol
            )
            
            if isinstance(open_orders_response, dict) and open_orders_response.get('retCode') == 0:
                orders = open_orders_response.get('result', {}).get('list', [])
                
                # Buscar órdenes que coincidan con el patrón base
                orders_to_cancel = []
                for order in orders:
                    order_link_id = order.get('orderLinkId', '')
                    if order_link_id.startswith(base_order_link_id):
                        orders_to_cancel.append(order)
                
                # Cancelar órdenes encontradas
                for order in orders_to_cancel:
                    order_id = order.get('orderId')
                    order_link_id = order.get('orderLinkId')
                    print(f"🗑️ Cancelando orden existente: {order_link_id} (ID: {order_id})")
                    
                    try:
                        cancel_response = self._execute_with_retry(
                            self.client.cancel_order,
                            category="linear",
                            symbol=symbol,
                            orderId=order_id
                        )
                        
                        if isinstance(cancel_response, dict) and cancel_response.get('retCode') == 0:
                            print(f"✅ Orden {order_link_id} cancelada exitosamente")
                        else:
                            print(f"⚠️ No se pudo cancelar orden {order_link_id}: {cancel_response.get('retMsg', 'Error desconocido')}")
                    except Exception as e:
                        print(f"⚠️ Error cancelando orden {order_link_id}: {str(e)}")
                
                if not orders_to_cancel:
                    print(f"✅ No se encontraron órdenes existentes para {base_order_link_id}")
            else:
                print(f"⚠️ No se pudieron obtener órdenes abiertas: {open_orders_response.get('retMsg', 'Error desconocido')}")
                
        except Exception as e:
            print(f"⚠️ Error verificando órdenes existentes: {str(e)}")
            # No lanzar excepción aquí, solo registrar el error

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
            
            response = self._execute_with_retry(
                self.client.get_positions,
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
        Obtiene el balance disponible para trading de futuros
        
        Returns:
            Diccionario con información del balance disponible
        """
        try:
            print("💰 Consultando balance de la cuenta UNIFIED para futuros...")
            
            response = self._execute_with_retry(
                self.client.get_wallet_balance,
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
                    
                    # Para futuros, usar totalAvailableBalance del account_info principal
                    total_available = account_info.get('totalAvailableBalance', '0')
                    
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
                                'transferBalance': safe_float(total_available, 0),  # Balance disponible para futuros
                                'bonus': safe_float(coin.get('bonus', 0)),
                                'equity': safe_float(coin.get('equity', 0)),
                                'usdValue': safe_float(coin.get('usdValue', 0))
                            }
                            print(f"✅ Balance USDT encontrado para futuros: {balance_info}")
                            print(f"💵 Balance disponible para trading: ${balance_info['transferBalance']}")
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
            response = self._execute_with_retry(
                self.client.get_tickers,
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
                    
                    # En testnet, usar indexPrice (precio real del mercado)
                    # En lugar de lastPrice (precio artificial del testnet)
                    index_price = ticker.get('indexPrice')
                    last_price = ticker.get('lastPrice')
                    
                    # Preferir indexPrice si está disponible (más preciso)
                    if index_price:
                        price = float(index_price)
                        print(f"✅ Precio índice para {symbol}: {price} (indexPrice)")
                        return price
                    elif last_price:
                        price = float(last_price)
                        print(f"✅ Precio último para {symbol}: {price} (lastPrice)")
                        return price
            
            print(f"⚠️ No se pudo obtener el precio para {symbol}")
            return None
        
        except Exception as e:
            print(f"💥 Error consultando precio para {symbol}: {str(e)}")
            raise Exception(f"Error consultando precio: {str(e)}")
    
    def execute_strategy(self, symbol: str, side: str, entry_price: float, take_profit: float, 
                        stop_loss: float, average_price: float, ticket: str, usdt_amount: float):
        """
        Ejecuta una estrategia de trading en Bybit con parámetros específicos.
        
        Args:
            symbol: Símbolo del par (ej: 'BTCUSDT')
            side: Dirección de la operación ('Buy' o 'Sell')
            entry_price: Precio de entrada
            take_profit: Precio de take profit
            stop_loss: Precio de stop loss
            average_price: Precio promedio
            ticket: Identificador del ticket/estrategia
            usdt_amount: Cantidad en USDT a invertir
            
        Returns:
            Diccionario con el resultado de la ejecución
        """
        try:
            print(f"🚀 Ejecutando estrategia {ticket} para {symbol}...")
            print(f"📊 Parámetros: Side={side}, Entry=${entry_price}, TP=${take_profit}, SL=${stop_loss}")
            print(f"💰 Cantidad: ${usdt_amount} USDT, Average=${average_price}")
            
            # Calcular la cantidad en base al precio de entrada y cantidad en USDT
            # Convertir a float para evitar problemas de tipos
            entry_price_float = float(entry_price)
            usdt_amount_float = float(usdt_amount)
            
            quantity = round(usdt_amount_float / entry_price_float, 6)
            print(f"📏 Cantidad calculada inicial: {quantity} {symbol.replace('USDT', '')}")
            
            # Definir cantidades mínimas según el símbolo
            min_quantities = {
                'BTCUSDT': 0.001,  # BTC mínimo
                'ETHUSDT': 0.01,   # ETH mínimo
                'BNBUSDT': 0.01    # BNB mínimo (estimado)
            }
            
            min_quantity = min_quantities.get(symbol, 0.001)  # Default 0.001
            min_notional = 5.0  # Valor mínimo en USDT para todas las órdenes
            
            # Verificar cantidad mínima
            if quantity < min_quantity:
                quantity = min_quantity
                actual_usdt = quantity * entry_price_float
                print(f"⚠️ Cantidad ajustada al mínimo: {quantity} {symbol.replace('USDT', '')} (${actual_usdt:.2f} USDT)")
            
            # Verificar valor nocional mínimo
            notional_value = quantity * entry_price_float
            if notional_value < min_notional:
                quantity = min_notional / entry_price_float
                quantity = max(quantity, min_quantity)  # Asegurar que no sea menor al mínimo
                actual_usdt = quantity * entry_price_float
                print(f"⚠️ Cantidad ajustada por valor nocional mínimo: {quantity} {symbol.replace('USDT', '')} (${actual_usdt:.2f} USDT)")
            
            # Redondear según el qtyStep del símbolo
            qty_steps = {
                'BTCUSDT': 0.001,  # BTC step
                'ETHUSDT': 0.01,   # ETH step
                'BNBUSDT': 0.01    # BNB step (estimado)
            }
            
            qty_step = qty_steps.get(symbol, 0.001)
            quantity = round(quantity / qty_step) * qty_step
            
            print(f"📏 Cantidad final: {quantity} {symbol.replace('USDT', '')}")
            
            # Validar parámetros
            if side not in ['Buy', 'Sell']:
                raise ValueError(f"Side debe ser 'Buy' o 'Sell', recibido: {side}")
            
            if usdt_amount <= 0:
                raise ValueError(f"La cantidad en USDT debe ser mayor a 0, recibido: {usdt_amount}")
            
            if entry_price_float <= 0:
                raise ValueError(f"El precio de entrada debe ser mayor a 0, recibido: {entry_price_float}")
            
            # Verificar balance disponible
            balance_info = self.get_available_balance()
            available_balance = balance_info.get('transferBalance', 0)
            
            if available_balance < usdt_amount:
                raise ValueError(f"Balance insuficiente. Disponible: ${available_balance}, Requerido: ${usdt_amount}")
            
            # Generar ID único con timestamp para evitar duplicados
            timestamp = int(time.time() * 1000)  # Timestamp en milisegundos
            unique_order_id = f"{ticket}_{symbol}_{side}_{timestamp}"
            
            # Cancelar órdenes existentes con el mismo patrón base para evitar duplicados
            base_order_id = f"{ticket}_{symbol}_{side}"
            self._cancel_existing_orders(symbol, base_order_id)
            
            # Crear orden principal con TP/SL integrados
            print(f"📝 Creando orden {side} para {symbol} con TP/SL integrados...")
            
            # Preparar parámetros de la orden
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": "Limit",
                "qty": str(quantity),
                "price": str(entry_price_float),
                "timeInForce": "GTC",
                "orderLinkId": unique_order_id,
                "reduceOnly": False
            }
            
            # Agregar Take Profit y Stop Loss si están definidos
            if take_profit > 0 or stop_loss > 0:
                order_params["tpslMode"] = "Full"  # Modo TP/SL requerido
                
            if take_profit > 0:
                order_params["takeProfit"] = str(take_profit)
                order_params["tpOrderType"] = "Market"  # Tipo de orden para TP (requerido con tpslMode Full)
                print(f"🎯 Take Profit configurado: ${take_profit}")
            
            if stop_loss > 0:
                order_params["stopLoss"] = str(stop_loss)
                order_params["slOrderType"] = "Market"  # Tipo de orden para SL
                print(f"🛑 Stop Loss configurado: ${stop_loss}")
            
            order_response = self._execute_with_retry(
                self.client.place_order,
                **order_params
            )
            
            print(f"📋 Respuesta orden principal: {order_response}")
            
            # Extraer información de la orden
            if isinstance(order_response, dict) and order_response.get('retCode') == 0:
                result = order_response.get('result', {})
                order_id = result.get('orderId')
                
                if order_id:
                    print(f"✅ Orden principal creada: {order_id}")
                    
                    # Verificar si TP/SL fueron creados exitosamente
                    tp_sl_result = {
                        'take_profit': {'success': take_profit > 0, 'price': take_profit} if take_profit > 0 else {'success': False},
                        'stop_loss': {'success': stop_loss > 0, 'price': stop_loss} if stop_loss > 0 else {'success': False}
                    }
                    
                    if take_profit > 0:
                        print(f"✅ Take Profit integrado en la orden: ${take_profit}")
                    if stop_loss > 0:
                        print(f"✅ Stop Loss integrado en la orden: ${stop_loss}")
                    
                    return {
                        'success': True,
                        'ticket': ticket,
                        'symbol': symbol,
                        'side': side,
                        'entry_price': entry_price_float,
                        'quantity': quantity,
                        'usdt_amount': usdt_amount,
                        'order_id': order_id,
                        'take_profit': take_profit,
                        'stop_loss': stop_loss,
                        'average_price': average_price,
                        'tp_sl_orders': tp_sl_result,
                        'message': f"Estrategia {ticket} ejecutada exitosamente con TP/SL integrados"
                    }
                else:
                    raise Exception(f"No se pudo obtener el ID de la orden: {order_response}")
            else:
                error_msg = order_response.get('retMsg', 'Error desconocido')
                raise Exception(f"Error creando orden: {error_msg}")
                
        except Exception as e:
            print(f"💥 Error ejecutando estrategia {ticket}: {str(e)}")
            return {
                'success': False,
                'ticket': ticket,
                'symbol': symbol,
                'error': str(e),
                'message': f"Error ejecutando estrategia {ticket}: {str(e)}"
            }
    
    def _create_tp_sl_orders(self, symbol: str, side: str, quantity: float, 
                           take_profit: float, stop_loss: float, ticket: str):
        """
        Crea órdenes de Take Profit y Stop Loss para una posición.
        
        Args:
            symbol: Símbolo del par
            side: Dirección de la orden original
            quantity: Cantidad de la posición
            take_profit: Precio de take profit
            stop_loss: Precio de stop loss
            ticket: Identificador del ticket
            
        Returns:
            Diccionario con el resultado de las órdenes TP/SL
        """
        try:
            print(f"🎯 Creando órdenes TP/SL para {symbol}...")
            
            # Determinar el lado opuesto para cerrar la posición
            close_side = "Sell" if side == "Buy" else "Buy"
            
            tp_sl_results = {}
            
            # Crear orden de Take Profit
            if take_profit > 0:
                # Generar ID único con timestamp para TP
                tp_timestamp = int(time.time() * 1000)
                tp_order_id = f"{ticket}_{symbol}_TP_{tp_timestamp}"
                
                # Cancelar órdenes TP existentes
                base_tp_id = f"{ticket}_{symbol}_TP"
                self._cancel_existing_orders(symbol, base_tp_id)
                
                print(f"🎯 Creando Take Profit a ${take_profit}...")
                tp_response = self._execute_with_retry(
                    self.client.place_order,
                    category="linear",
                    symbol=symbol,
                    side=close_side,
                    orderType="Limit",
                    qty=str(quantity),
                    price=str(take_profit),
                    timeInForce="GTC",
                    orderLinkId=tp_order_id,
                    reduceOnly=False  # Cambiar a False para permitir la orden sin posición existente
                )
                
                if isinstance(tp_response, dict) and tp_response.get('retCode') == 0:
                    tp_order_id = tp_response.get('result', {}).get('orderId')
                    tp_sl_results['take_profit'] = {
                        'success': True,
                        'order_id': tp_order_id,
                        'price': take_profit
                    }
                    print(f"✅ Take Profit creado: {tp_order_id}")
                else:
                    tp_sl_results['take_profit'] = {
                        'success': False,
                        'error': tp_response.get('retMsg', 'Error desconocido')
                    }
            
            # Crear orden de Stop Loss
            if stop_loss > 0:
                # Generar ID único con timestamp para SL
                sl_timestamp = int(time.time() * 1000)
                sl_order_id = f"{ticket}_{symbol}_SL_{sl_timestamp}"
                
                # Cancelar órdenes SL existentes
                base_sl_id = f"{ticket}_{symbol}_SL"
                self._cancel_existing_orders(symbol, base_sl_id)
                
                print(f"🛑 Creando Stop Loss a ${stop_loss}...")
                sl_response = self._execute_with_retry(
                    self.client.place_order,
                    category="linear",
                    symbol=symbol,
                    side=close_side,
                    orderType="StopMarket",  # Usar StopMarket para stop loss
                    qty=str(quantity),
                    stopLoss=str(stop_loss),
                    timeInForce="GTC",
                    orderLinkId=sl_order_id,
                    reduceOnly=False  # Cambiar a False para permitir la orden sin posición existente
                )
                
                if isinstance(sl_response, dict) and sl_response.get('retCode') == 0:
                    sl_order_id = sl_response.get('result', {}).get('orderId')
                    tp_sl_results['stop_loss'] = {
                        'success': True,
                        'order_id': sl_order_id,
                        'price': stop_loss
                    }
                    print(f"✅ Stop Loss creado: {sl_order_id}")
                else:
                    tp_sl_results['stop_loss'] = {
                        'success': False,
                        'error': sl_response.get('retMsg', 'Error desconocido')
                    }
            
            return tp_sl_results
            
        except Exception as e:
            print(f"💥 Error creando órdenes TP/SL: {str(e)}")
            return {
                'take_profit': {'success': False, 'error': str(e)},
                'stop_loss': {'success': False, 'error': str(e)}
            }

