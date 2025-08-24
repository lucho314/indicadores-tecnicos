import pandas as pd
import pandas_ta as ta
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TechnicalIndicatorsCalculator:
    """
    Calculadora de indicadores técnicos usando pandas_ta
    Calcula: EMA20, EMA200, RSI14, MACD, Bollinger Bands, ATR14, OBV, ADX14
    """
    
    def __init__(self):
        self.required_periods = 200  # Necesitamos al menos 200 períodos para EMA200
        
    def calculate_all_indicators(self, klines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula todos los indicadores técnicos para las velas proporcionadas
        
        Args:
            klines: Lista de velas ordenadas por tiempo (más antigua primero)
            
        Returns:
            Diccionario con todos los indicadores calculados
        """
        if len(klines) < 20:
            raise ValueError(f"Se necesitan al menos 20 velas, recibidas: {len(klines)}")
            
        try:
            # Convertir a DataFrame
            df = self._klines_to_dataframe(klines)
            
            if df.empty:
                raise ValueError("DataFrame vacío después de conversión")
                
            logger.info(f"📊 Calculando indicadores para {len(df)} velas")
            
            # Calcular todos los indicadores
            indicators = {}
            
            # Información básica de la última vela cerrada
            last_candle = df.iloc[-1]
            indicators.update({
                "timestamp": last_candle.name,  # El timestamp está en el índice
                "symbol": klines[-1].get("symbol", "BTCUSDT"),
                "interval": klines[-1].get("interval_type", "240"),
                "open_price": float(last_candle["open"]),
                "high_price": float(last_candle["high"]),
                "low_price": float(last_candle["low"]),
                "close_price": float(last_candle["close"]),
                "volume": float(last_candle["volume"])
            })
            
            # SMA 20, 50 y 200
            indicators.update(self._calculate_sma(df))
            
            # EMA 20 y 200
            indicators.update(self._calculate_ema(df))
            
            # RSI 14
            indicators.update(self._calculate_rsi(df))
            
            # MACD
            indicators.update(self._calculate_macd(df))
            
            # Bollinger Bands
            indicators.update(self._calculate_bollinger_bands(df))
            
            # ATR 14
            indicators.update(self._calculate_atr(df))
            
            # OBV
            indicators.update(self._calculate_obv(df))
            
            # ADX 14
            indicators.update(self._calculate_adx(df))
            
            logger.info(f"✅ Indicadores calculados exitosamente")
            logger.debug(f"Indicadores: RSI={indicators.get('rsi14'):.2f}, EMA20={indicators.get('ema20'):.2f}")
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ Error calculando indicadores: {e}")
            raise
            
    def _klines_to_dataframe(self, klines: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convierte lista de velas a DataFrame de pandas
        """
        try:
            data = []
            for kline in klines:
                data.append({
                    "timestamp": datetime.fromtimestamp(kline["open_time"] / 1000),
                    "open": float(kline["open_price"]),
                    "high": float(kline["high_price"]),
                    "low": float(kline["low_price"]),
                    "close": float(kline["close_price"]),
                    "volume": float(kline["volume"])
                })
                
            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error convirtiendo a DataFrame: {e}")
            raise
            
    def _calculate_sma(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula SMA (Simple Moving Average) para diferentes períodos
        """
        try:
            sma20 = ta.sma(df["close"], length=20)
            sma50 = ta.sma(df["close"], length=50) if len(df) >= 50 else None
            sma200 = ta.sma(df["close"], length=200) if len(df) >= 200 else None
            
            result = {
                "sma20": float(sma20.iloc[-1]) if not sma20.empty else None
            }
            
            if sma50 is not None and not sma50.empty:
                result["sma50"] = float(sma50.iloc[-1])
            else:
                result["sma50"] = None
                
            if sma200 is not None and not sma200.empty:
                result["sma200"] = float(sma200.iloc[-1])
            else:
                result["sma200"] = None
                logger.warning(f"SMA200 no calculada - se necesitan 200 períodos, disponibles: {len(df)}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calculando SMA: {e}")
            return {"sma20": None, "sma50": None, "sma200": None}
            
    def _calculate_ema(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula EMA 20 y EMA 200
        """
        try:
            ema20 = ta.ema(df["close"], length=20)
            ema200 = ta.ema(df["close"], length=200) if len(df) >= 200 else None
            
            result = {
                "ema20": float(ema20.iloc[-1]) if not ema20.empty else None
            }
            
            if ema200 is not None and not ema200.empty:
                result["ema200"] = float(ema200.iloc[-1])
            else:
                result["ema200"] = None
                logger.warning(f"EMA200 no calculada - se necesitan 200 períodos, disponibles: {len(df)}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calculando EMA: {e}")
            return {"ema20": None, "ema200": None}
            
    def _calculate_rsi(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula RSI 14
        """
        try:
            rsi = ta.rsi(df["close"], length=14)
            
            return {
                "rsi14": float(rsi.iloc[-1]) if not rsi.empty else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculando RSI: {e}")
            return {"rsi14": None}
            
    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula MACD (12, 26, 9)
        """
        try:
            macd_data = ta.macd(df["close"], fast=12, slow=26, signal=9)
            
            if macd_data is not None and not macd_data.empty:
                return {
                    "macd": float(macd_data["MACD_12_26_9"].iloc[-1]),
                    "macd_signal": float(macd_data["MACDs_12_26_9"].iloc[-1]),
                    "macd_histogram": float(macd_data["MACDh_12_26_9"].iloc[-1])
                }
            else:
                return {"macd": None, "macd_signal": None, "macd_histogram": None}
                
        except Exception as e:
            logger.error(f"❌ Error calculando MACD: {e}")
            return {"macd": None, "macd_signal": None, "macd_histogram": None}
            
    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula Bollinger Bands (20, 2)
        """
        try:
            bb = ta.bbands(df["close"], length=20, std=2)
            
            if bb is not None and not bb.empty:
                return {
                    "bb_upper": float(bb["BBU_20_2.0"].iloc[-1]),
                    "bb_middle": float(bb["BBM_20_2.0"].iloc[-1]),
                    "bb_lower": float(bb["BBL_20_2.0"].iloc[-1]),
                    "bb_width": float(bb["BBB_20_2.0"].iloc[-1]),
                    "bb_percent": float(bb["BBP_20_2.0"].iloc[-1])
                }
            else:
                return {
                    "bb_upper": None, "bb_middle": None, "bb_lower": None,
                    "bb_width": None, "bb_percent": None
                }
                
        except Exception as e:
            logger.error(f"❌ Error calculando Bollinger Bands: {e}")
            return {
                "bb_upper": None, "bb_middle": None, "bb_lower": None,
                "bb_width": None, "bb_percent": None
            }
            
    def _calculate_atr(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula ATR 14 (Average True Range)
        """
        try:
            atr = ta.atr(df["high"], df["low"], df["close"], length=14)
            
            return {
                "atr14": float(atr.iloc[-1]) if not atr.empty else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculando ATR: {e}")
            return {"atr14": None}
            
    def _calculate_obv(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula OBV (On Balance Volume)
        """
        try:
            obv = ta.obv(df["close"], df["volume"])
            
            return {
                "obv": float(obv.iloc[-1]) if not obv.empty else None
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculando OBV: {e}")
            return {"obv": None}
            
    def _calculate_adx(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula ADX 14 (Average Directional Index)
        """
        try:
            adx_data = ta.adx(df["high"], df["low"], df["close"], length=14)
            
            if adx_data is not None and not adx_data.empty:
                return {
                    "adx14": float(adx_data["ADX_14"].iloc[-1]),
                    "dmp14": float(adx_data["DMP_14"].iloc[-1]),  # Directional Movement Positive
                    "dmn14": float(adx_data["DMN_14"].iloc[-1])   # Directional Movement Negative
                }
            else:
                return {"adx14": None, "dmp14": None, "dmn14": None}
                
        except Exception as e:
            logger.error(f"❌ Error calculando ADX: {e}")
            return {"adx14": None, "dmp14": None, "dmn14": None}
            
    def get_trend_analysis(self, indicators: Dict[str, Any]) -> Dict[str, str]:
        """
        Análisis básico de tendencia basado en los indicadores
        
        Returns:
            Diccionario con análisis de tendencia
        """
        try:
            analysis = {}
            
            # Análisis EMA
            if indicators.get("ema20") and indicators.get("ema200"):
                if indicators["ema20"] > indicators["ema200"]:
                    analysis["ema_trend"] = "bullish"
                else:
                    analysis["ema_trend"] = "bearish"
            else:
                analysis["ema_trend"] = "neutral"
                
            # Análisis RSI
            rsi = indicators.get("rsi14")
            if rsi:
                if rsi > 70:
                    analysis["rsi_signal"] = "overbought"
                elif rsi < 30:
                    analysis["rsi_signal"] = "oversold"
                else:
                    analysis["rsi_signal"] = "neutral"
            else:
                analysis["rsi_signal"] = "unknown"
                
            # Análisis MACD
            macd = indicators.get("macd")
            macd_signal = indicators.get("macd_signal")
            if macd and macd_signal:
                if macd > macd_signal:
                    analysis["macd_signal"] = "bullish"
                else:
                    analysis["macd_signal"] = "bearish"
            else:
                analysis["macd_signal"] = "unknown"
                
            # Análisis ADX
            adx = indicators.get("adx14")
            if adx:
                if adx > 25:
                    analysis["trend_strength"] = "strong"
                elif adx > 20:
                    analysis["trend_strength"] = "moderate"
                else:
                    analysis["trend_strength"] = "weak"
            else:
                analysis["trend_strength"] = "unknown"
                
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error en análisis de tendencia: {e}")
            return {}
            
    def validate_indicators(self, indicators: Dict[str, Any]) -> bool:
        """
        Valida que los indicadores calculados sean válidos
        
        Returns:
            True si los indicadores son válidos
        """
        required_fields = ["close_price", "rsi14", "ema20", "macd"]
        
        for field in required_fields:
            if field not in indicators or indicators[field] is None:
                logger.warning(f"⚠️ Campo requerido faltante o nulo: {field}")
                return False
                
        # Validar rangos
        rsi = indicators.get("rsi14")
        if rsi and (rsi < 0 or rsi > 100):
            logger.warning(f"⚠️ RSI fuera de rango: {rsi}")
            return False
            
        close_price = indicators.get("close_price")
        if close_price and close_price <= 0:
            logger.warning(f"⚠️ Precio de cierre inválido: {close_price}")
            return False
            
        return True