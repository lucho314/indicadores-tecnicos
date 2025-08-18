import time
import requests
from typing import Dict, Any, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import API_KEY, SYMBOL, INTERVAL  # p.ej. "BTC/USD", "1h"

BASE = "https://api.twelvedata.com"
ENDPOINTS = {
    "rsi":    "/rsi",
    "macd":   "/macd",
    "sma":    "/sma",
    "adx":    "/adx",
    "bbands": "/bbands",
    "price":  "/price",  # Para obtener el precio actual
}

def _build_session(total_retries: int = 3, backoff: float = 0.5) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"])
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=5)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

def _fetch_indicator(
    session: requests.Session,
    name: str,
    symbol: str,
    interval: str,
    apikey: str,
    timeout: float = 10.0,
) -> Tuple[str, Dict[str, Any]]:
    """Devuelve (nombre, payload_json_o_error)"""
    url = f"{BASE}{ENDPOINTS[name]}"
    params = {"symbol": symbol, "interval": interval, "apikey": apikey}
    try:
        r = session.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        # Normalizar formato de error de Twelve Data
        if isinstance(data, dict) and "status" in data and data["status"] == "error":
            return name, {"error": data.get("message", "unknown error")}
        if "code" in data and "message" in data:  # otro formato de error
            return name, {"error": data["message"], "code": data.get("code")}
        return name, data
    except Exception as e:
        return name, {"error": str(e)}

def _latest_common_timestamp(payloads: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """Encuentra el último timestamp común entre todos los indicadores (campo 'values' con 'datetime')."""
    sets = []
    for v in payloads.values():
        vals = v.get("values")
        if not isinstance(vals, list):
            return None
        ts = {row.get("datetime") for row in vals if isinstance(row, dict) and "datetime" in row}
        if not ts:
            return None
        sets.append(ts)
    common = set.intersection(*sets) if sets else set()
    if not common:
        return None
    # Devolver el más reciente
    return sorted(common)[-1]

def _pick_value_at(values: list, ts: str, key: Optional[str] = None) -> Optional[float]:
    for row in values:
        if row.get("datetime") == ts:
            if key is None:
                # cuando el indicador tiene un único valor principal, suele venir como 'value'
                val = row.get("value")
                return float(val) if val is not None else None
            # algunos como MACD/BBANDS tienen varias claves
            val = row.get(key)
            return float(val) if val is not None else None
    return None

def obtener_indicadores(symbol: str = SYMBOL or "BTC/USD", interval: str = INTERVAL or "1h") -> Dict[str, Any]:
    if not API_KEY:
        return {"symbol": symbol, "interval": interval, "errors": {"config": "API_KEY no configurada"}}
        
    session = _build_session()
    results: Dict[str, Dict[str, Any]] = {}

    # Descargas (secuencial con retry; si querés, podés paralelizar con threads)
    for name in ENDPOINTS.keys():
        k, data = _fetch_indicator(session, name, symbol, interval, API_KEY)
        results[k] = data
        # Si estás en plan gratuito, una pausa suave ayuda a evitar 429
        time.sleep(0.2)

    # Si hay errores, devuélvelos todos y no intentes cruzar
    errors = {k: v for k, v in results.items() if isinstance(v, dict) and v.get("error")}
    if errors:
        return {"symbol": symbol, "interval": interval, "errors": errors}

    # Asegurate de tener 'values' en todos (excepto price que tiene formato diferente)
    indicators_with_values = {k: v for k, v in results.items() if k != "price"}
    if not all(isinstance(indicators_with_values[k].get("values"), list) for k in indicators_with_values):
        return {"symbol": symbol, "interval": interval, "errors": {"format": "faltan 'values' en alguna respuesta"}}

    # Encontrar timestamp común (excluyendo price que tiene formato diferente)
    indicators_for_timestamp = {k: v for k, v in results.items() if k != "price"}
    ts = _latest_common_timestamp(indicators_for_timestamp)
    if not ts:
        return {"symbol": symbol, "interval": interval, "errors": {"sync": "no hay timestamp común entre indicadores"}}

    # Extraer valores
    rsi = _pick_value_at(results["rsi"]["values"], ts, key="rsi")  # RSI usa clave "rsi"
    sma = _pick_value_at(results["sma"]["values"], ts, key="sma")  # SMA usa clave "sma"
    adx = _pick_value_at(results["adx"]["values"], ts, key="adx")  # ADX usa clave "adx"

    # MACD suele traer 'macd', 'macd_signal', 'macd_hist'
    macd = _pick_value_at(results["macd"]["values"], ts, key="macd")
    macd_signal = _pick_value_at(results["macd"]["values"], ts, key="macd_signal")
    macd_hist = _pick_value_at(results["macd"]["values"], ts, key="macd_hist")

    # Bandas de Bollinger: 'upper_band', 'middle_band', 'lower_band'
    bb_u = _pick_value_at(results["bbands"]["values"], ts, key="upper_band")
    bb_m = _pick_value_at(results["bbands"]["values"], ts, key="middle_band")
    bb_l = _pick_value_at(results["bbands"]["values"], ts, key="lower_band")

    # Precio actual - la API de /price devuelve formato diferente: {"price": "value"}
    close_price = None
    if "price" in results:
        price_data = results["price"]
        if isinstance(price_data, dict):
            # Formato directo: {"price": "4412.59"}
            if "price" in price_data:
                try:
                    close_price = float(price_data["price"])
                except (ValueError, TypeError):
                    close_price = None
            # Formato con values (por si acaso)
            elif "values" in price_data and price_data["values"]:
                close_price = _pick_value_at(price_data["values"], ts, key="close")
    
    # Si no hay precio del endpoint /price, usar middle band como aproximación
    if close_price is None and bb_m is not None:
        close_price = bb_m

    return {
        "symbol": symbol,
        "interval": interval,
        "timestamp": ts,
        "rsi": rsi,
        "sma": sma,
        "adx": adx,
        "macd": macd,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "bb_upper": bb_u,
        "bb_middle": bb_m,
        "bb_lower": bb_l,
        "close_price": close_price,
    }

if __name__ == "__main__":
    data = obtener_indicadores()
    print(data)
