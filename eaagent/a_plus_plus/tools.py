import os
import time
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Literal, List
from dotenv import load_dotenv

import tushare as ts

load_dotenv()

USE_MOCK_DATA = os.getenv("USE_MOCK_OBSERVATION", "false").lower() == "true"

_observation_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 90


def _get_cache_key(symbol: str, period: str, lookback: int) -> str:
    return f"{symbol.upper()}_{period}_{lookback}"


def _get_from_cache(key: str) -> Optional[Dict[str, Any]]:
    if key in _observation_cache:
        cached = _observation_cache[key]
        if time.time() - cached["timestamp"] < CACHE_TTL:
            return cached["data"]
        else:
            del _observation_cache[key]
    return None


def _save_to_cache(key: str, data: Dict[str, Any]):
    _observation_cache[key] = {
        "data": data,
        "timestamp": time.time()
    }


def _get_mock_klines(symbol: str, period: str, lookback: int = 60) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now().normalize(), periods=lookback, freq='D')
    base_price = 3100 if symbol.startswith("RB") else 780
    close = np.cumsum(np.random.randn(lookback) * 8) + base_price
    high = close + np.abs(np.random.randn(lookback) * 6)
    low = close - np.abs(np.random.randn(lookback) * 6)
    open_ = close + np.random.randn(lookback) * 4

    df = pd.DataFrame({
        'trade_date': dates,
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'vol': np.random.randint(300, 1200, lookback),
        'oi': np.random.randint(3000, 6000, lookback)
    })
    return df


def _get_mock_observation(symbol: str) -> Dict[str, Any]:
    mock_data = {
        "RB2605": {
            "latest_price": 3150.0, "price_change": 12.0, "price_change_pct": 0.38,
            "volume_change": 1240, "oi_change": -380, "volume_change_pct": 18.5,
            "atr": 38.2, "ma20": 3128.5,
            "key_levels": {
                "resistances": [{"price": 3295.0, "index": 45}, {"price": 3220.0, "index": 52}],
                "supports": [{"price": 3065.0, "index": 38}, {"price": 3120.0, "index": 55}],
                "key_levels_text": "压力位：3295 / 3220 | 支撑位：3065 / 3120"
            }
        }
    }
    data = mock_data.get(symbol.upper(), mock_data["RB2605"])
    text = f"""【{symbol} 模拟结构化观察】
- 最新收盘: {data['latest_price']} | 价格变化: {data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)
- 成交量变化 {data['volume_change']:+d} ({data['volume_change_pct']:+.1f}%), 持仓量变化 {data['oi_change']:+d}
- ATR: {data['atr']} | MA20: {data['ma20']}
- {data['key_levels']['key_levels_text']}"""
    return {
        "symbol": symbol, "status": "mock",
        "latest_price": data['latest_price'],
        "price_change": data['price_change'],
        "volume_oi": data.get('volume_oi', {}),
        "atr": data['atr'], "ma20": data['ma20'],
        "key_levels": data['key_levels'],
        "observation_text": text.strip()
    }


def get_pro_api():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError("TUSHARE_TOKEN 未在 .env 中配置")
    ts.set_token(token)
    return ts.pro_api()


def get_futures_klines(
    symbol: str,
    period: Literal["D", "30"] = "D",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 300,
    max_retry: int = 2
) -> pd.DataFrame:
    if USE_MOCK_DATA:
        return _get_mock_klines(symbol, period, lookback=limit)

    ts_code = symbol.upper().strip()
    if "." not in ts_code:
        ts_code = f"{ts_code}.SHF"

    for attempt in range(max_retry + 1):
        try:
            pro = get_pro_api()
            if period == "D":
                df = pro.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, limit=limit)
            else:
                df = pro.fut_min(ts_code=ts_code, freq="30min", start_date=start_date, end_date=end_date, limit=limit)

            if df is not None and not df.empty:
                return df.sort_values("trade_date").reset_index(drop=True)
        except Exception as e:
            print(f"[尝试 {attempt+1}] 获取 {ts_code} ({period}) 失败: {str(e)[:100]}")
            if "频率超限" in str(e):
                time.sleep(75)
            elif attempt < max_retry:
                time.sleep(4)
    return pd.DataFrame()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    if df.empty or len(df) < period + 1:
        return None
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr_series = tr.rolling(window=period).mean()
    return round(atr_series.dropna().iloc[-1], 2) if not atr_series.dropna().empty else None


def calculate_ma(df: pd.DataFrame, period: int = 20) -> Optional[float]:
    if df.empty or len(df) < period:
        return None
    ma = df["close"].rolling(window=period).mean()
    return round(ma.iloc[-1], 2) if not ma.dropna().empty else None


def calculate_volume_oi_change(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty or len(df) < 2:
        return {"volume_change": 0, "oi_change": 0, "volume_change_pct": 0, "summary": "数据不足"}
    latest, prev = df.iloc[-1], df.iloc[-2]
    vol_change = int(latest.get("vol", 0) - prev.get("vol", 0))
    oi_change = int(latest.get("oi", 0) - prev.get("oi", 0))
    vol_pct = round(vol_change / max(prev.get("vol", 1), 1) * 100, 1)
    return {
        "volume_change": vol_change, "oi_change": oi_change,
        "volume_change_pct": vol_pct,
        "summary": f"成交量变化 {vol_change:+d} ({vol_pct:+.1f}%), 持仓量变化 {oi_change:+d}"
    }


def detect_key_levels(df: pd.DataFrame, lookback: int = 60, num_levels: int = 3) -> Dict[str, Any]:
    """
    返回支撑压力位 + 每个水平对应的K线位置（用于画射线）
    """
    if df.empty or len(df) < 20:
        return {"resistances": [], "supports": [], "key_levels_text": "数据不足"}

    recent_df = df.tail(lookback).reset_index(drop=True)
    highs = recent_df["high"].values
    lows = recent_df["low"].values
    closes = recent_df["close"].values
    current_price = closes[-1]

    resistances = []
    supports = []

    for i in range(2, len(recent_df) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            resistances.append({"price": round(highs[i], 2), "index": i})
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            supports.append({"price": round(lows[i], 2), "index": i})

    # 按距离当前价格排序，取最近的几个
    resistances = sorted(resistances, key=lambda x: abs(x["price"] - current_price))[:num_levels]
    supports = sorted(supports, key=lambda x: abs(x["price"] - current_price))[:num_levels]

    # 重新按价格从高到低 / 低到高排序
    resistances = sorted(resistances, key=lambda x: x["price"], reverse=True)
    supports = sorted(supports, key=lambda x: x["price"])

    res_str = " / ".join([str(r["price"]) for r in resistances]) if resistances else "无"
    sup_str = " / ".join([str(s["price"]) for s in supports]) if supports else "无"

    return {
        "resistances": resistances,
        "supports": supports,
        "key_levels_text": f"压力位：{res_str} | 支撑位：{sup_str}"
    }


def get_structured_observation(
    symbol: str,
    period: Literal["D", "30"] = "D",
    lookback: Optional[int] = None
) -> Dict[str, Any]:
    if USE_MOCK_DATA:
        return _get_mock_observation(symbol)

    if lookback is None:
        lookback = 60 if period == "D" else 40

    cache_key = _get_cache_key(symbol, period, lookback)
    cached = _get_from_cache(cache_key)
    if cached is not None:
        return cached

    df = get_futures_klines(symbol=symbol, period=period, limit=lookback + 5)

    if df.empty:
        return {
            "symbol": symbol, "status": "error", "period": period,
            "observation_text": f"【{symbol}】无法获取 {period} 数据"
        }

    vol_oi = calculate_volume_oi_change(df)
    atr = calculate_atr(df)
    ma20 = calculate_ma(df, 20)
    key_levels = detect_key_levels(df, lookback=lookback)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    price_chg = round(latest["close"] - prev["close"], 2)
    price_pct = round(price_chg / prev["close"] * 100, 2) if prev["close"] > 0 else 0

    text = f"""【{symbol} {period} 结构化观察】
- 最新收盘: {latest['close']} | 价格变化: {price_chg:+.2f} ({price_pct:+.2f}%)
- {vol_oi['summary']}
- ATR: {atr} | MA20: {ma20}
- {key_levels['key_levels_text']}"""

    result = {
        "symbol": symbol, "status": "success", "period": period,
        "latest_price": latest["close"], "price_change": price_chg,
        "volume_oi": vol_oi, "atr": atr, "ma20": ma20,
        "key_levels": key_levels,
        "observation_text": text.strip()
    }
    _save_to_cache(cache_key, result)
    return result


def get_latest_observation(symbol: str, period: Literal["D", "30"] = "D", lookback: Optional[int] = None) -> str:
    if lookback is None:
        lookback = 60 if period == "D" else 40
    result = get_structured_observation(symbol, period, lookback)
    return result.get("observation_text", "获取失败")
