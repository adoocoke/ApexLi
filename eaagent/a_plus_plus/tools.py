import os
import time
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Literal
from dotenv import load_dotenv

import tushare as ts

load_dotenv()

# ==================== 配置 ====================
USE_MOCK_DATA = os.getenv("USE_MOCK_OBSERVATION", "false").lower() == "true"

# ==================== 内存缓存 ====================
_observation_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL = 90  # 缓存时间（秒），30分钟数据建议缓存久一点


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


# ==================== Mock 数据 ====================

def _get_mock_observation(symbol: str) -> Dict[str, Any]:
    mock_data = {
        "RB2605": {
            "latest_price": 3150.0, "price_change": 12.0, "price_change_pct": 0.38,
            "volume_change": 1240, "oi_change": -380, "volume_change_pct": 18.5,
            "atr": 38.2, "ma20": 3128.5, "recent_high": 3295.0, "recent_low": 3065.0,
        },
        "RB2609": {
            "latest_price": 3142.0, "price_change": -8.0, "price_change_pct": -0.25,
            "volume_change": -5320, "oi_change": 1850, "volume_change_pct": -9.2,
            "atr": 29.8, "ma20": 3165.3, "recent_high": 3278.0, "recent_low": 3115.0,
        },
        "I2609": {
            "latest_price": 785.5, "price_change": 6.5, "price_change_pct": 0.83,
            "volume_change": 890, "oi_change": 420, "volume_change_pct": 12.4,
            "atr": 12.8, "ma20": 772.3, "recent_high": 812.0, "recent_low": 745.0,
        }
    }

    data = mock_data.get(symbol.upper(), mock_data["RB2605"])

    text = f"""【{symbol} 模拟结构化观察】
- 最新收盘: {data['latest_price']} | 价格变化: {data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)
- 成交量变化 {data['volume_change']:+d} ({data['volume_change_pct']:+.1f}%), 持仓量变化 {data['oi_change']:+d}
- ATR: {data['atr']} | MA20: {data['ma20']}
- 近期关键位: 高 {data['recent_high']}, 低 {data['recent_low']}"""

    return {
        "symbol": symbol,
        "status": "mock",
        "latest_price": data['latest_price'],
        "price_change": data['price_change'],
        "volume_oi": {
            "volume_change": data['volume_change'],
            "oi_change": data['oi_change'],
            "volume_change_pct": data['volume_change_pct'],
            "summary": f"成交量变化 {data['volume_change']:+d} ({data['volume_change_pct']:+.1f}%), 持仓量变化 {data['oi_change']:+d}"
        },
        "atr": data['atr'],
        "ma20": data['ma20'],
        "key_levels": {
            "recent_high": data['recent_high'],
            "recent_low": data['recent_low']
        },
        "observation_text": text.strip()
    }


# ==================== Tushare 真实接口（重点支持日线 + 30分钟） ====================

def get_pro_api():
    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError("TUSHARE_TOKEN 未在 .env 中配置")
    ts.set_token(token)
    return ts.pro_api()


def get_futures_klines(
    symbol: str,
    period: Literal["D", "30"] = "D",   # 目前重点支持 日线 和 30分钟
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 300,
    max_retry: int = 2
) -> pd.DataFrame:
    """
    获取期货K线数据（当前重点支持日线和30分钟）
    """
    ts_code = symbol.upper().strip()
    if "." not in ts_code:
        ts_code = f"{ts_code}.SHF"

    for attempt in range(max_retry + 1):
        try:
            pro = get_pro_api()

            if period == "D":
                # 日线优先使用 fut_daily（更稳定）
                df = pro.fut_daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit
                )
            else:
                # 30分钟
                df = pro.fut_min(
                    ts_code=ts_code,
                    freq="30min",
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit
                )

            if df is not None and not df.empty:
                return df.sort_values("trade_date").reset_index(drop=True)

        except Exception as e:
            err_msg = str(e)
            print(f"[尝试 {attempt+1}] 获取 {ts_code} ({period}) 失败: {err_msg[:120]}")

            if "频率超限" in err_msg:
                print("检测到频率限制，暂停较长时间...")
                time.sleep(75)
            elif attempt < max_retry:
                time.sleep(4)

    return pd.DataFrame()


# ==================== 技术指标 ====================

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
        "volume_change": vol_change,
        "oi_change": oi_change,
        "volume_change_pct": vol_pct,
        "summary": f"成交量变化 {vol_change:+d} ({vol_pct:+.1f}%), 持仓量变化 {oi_change:+d}"
    }


def detect_key_levels(df: pd.DataFrame, lookback: int = 20) -> Dict[str, Any]:
    if df.empty or len(df) < lookback:
        return {"recent_high": None, "recent_low": None}
    recent = df.tail(lookback)
    return {
        "recent_high": round(recent["high"].max(), 2),
        "recent_low": round(recent["low"].min(), 2)
    }


# ==================== 结构化 Observation ====================

def get_structured_observation(
    symbol: str,
    period: Literal["D", "30"] = "D",
    lookback: int = 20
) -> Dict[str, Any]:
    # Mock 模式
    if USE_MOCK_DATA:
        return _get_mock_observation(symbol)

    cache_key = _get_cache_key(symbol, period, lookback)
    cached = _get_from_cache(cache_key)
    if cached is not None:
        print(f"[Cache Hit] 使用缓存数据: {symbol} ({period})")
        return cached

    df = get_futures_klines(symbol=symbol, period=period, limit=lookback + 5)

    if df.empty:
        result = {
            "symbol": symbol,
            "status": "error",
            "observation_text": f"【{symbol}】无法获取 {period} 数据，请检查合约或 Tushare 权限。"
        }
        _save_to_cache(cache_key, result)
        return result

    vol_oi = calculate_volume_oi_change(df)
    atr = calculate_atr(df)
    ma20 = calculate_ma(df, 20)
    key_levels = detect_key_levels(df)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    price_chg = round(latest["close"] - prev["close"], 2)
    price_pct = round(price_chg / prev["close"] * 100, 2) if prev["close"] > 0 else 0

    text = f"""【{symbol} {period} 结构化观察】
- 最新收盘: {latest['close']} | 价格变化: {price_chg:+.2f} ({price_pct:+.2f}%)
- {vol_oi['summary']}
- ATR: {atr} | MA20: {ma20}
- 近期关键位: 高 {key_levels['recent_high']}, 低 {key_levels['recent_low']}"""

    result = {
        "symbol": symbol,
        "status": "success",
        "period": period,
        "latest_price": latest["close"],
        "price_change": price_chg,
        "volume_oi": vol_oi,
        "atr": atr,
        "ma20": ma20,
        "key_levels": key_levels,
        "observation_text": text.strip()
    }

    _save_to_cache(cache_key, result)
    return result


def get_latest_observation(symbol: str, period: Literal["D", "30"] = "D", lookback: int = 5) -> str:
    result = get_structured_observation(symbol, period, lookback)
    return result.get("observation_text", "获取失败")
