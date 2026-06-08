import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Literal
from dotenv import load_dotenv

import tushare as ts

load_dotenv()

_pro_api = None


def get_pro_api():
    global _pro_api
    if _pro_api is None:
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("TUSHARE_TOKEN 未在 .env 中配置")
        ts.set_token(token)
        _pro_api = ts.pro_api()
    return _pro_api


def _normalize_ts_code(symbol: str) -> str:
    symbol = symbol.upper().strip()
    if "." in symbol:
        return symbol
    return f"{symbol}.SHF"


def get_futures_klines(
    symbol: str,
    period: Literal["D", "60", "30", "15", "5"] = "D",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 300
) -> pd.DataFrame:
    pro = get_pro_api()
    ts_code = _normalize_ts_code(symbol)

    df = pd.DataFrame()

    # 优先使用 pro_bar
    try:
        df = ts.pro_bar(
            ts_code=ts_code,
            asset="FT",
            start_date=start_date,
            end_date=end_date,
            freq=period if period != "D" else "D"
        )
        if df is not None and not df.empty:
            return df.sort_values("trade_date").reset_index(drop=True)
    except Exception as e:
        print(f"[pro_bar Warning] {str(e)[:100]}")

    # 备用：fut_daily
    try:
        if period == "D":
            df = pro.fut_daily(ts_code=ts_code, start_date=start_date, end_date=end_date, limit=limit)
            if df is not None and not df.empty:
                return df.sort_values("trade_date").reset_index(drop=True)
    except Exception as e:
        print(f"[fut_daily Error] {str(e)[:100]}")

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


def get_structured_observation(symbol: str, period: str = "D", lookback: int = 20) -> Dict[str, Any]:
    df = get_futures_klines(symbol=symbol, period=period, limit=lookback + 5)

    if df.empty:
        return {
            "symbol": symbol,
            "status": "error",
            "observation_text": f"【{symbol}】无法获取数据，请检查合约代码或 Tushare 权限。"
        }

    vol_oi = calculate_volume_oi_change(df)
    atr = calculate_atr(df)
    ma20 = calculate_ma(df, 20)
    key_levels = detect_key_levels(df)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    price_chg = round(latest["close"] - prev["close"], 2)
    price_pct = round(price_chg / prev["close"] * 100, 2) if prev["close"] > 0 else 0

    text = f"""【{symbol} 结构化观察】
- 最新收盘: {latest['close']} | 价格变化: {price_chg:+.2f} ({price_pct:+.2f}%)
- {vol_oi['summary']}
- ATR: {atr} | MA20: {ma20}
- 近期关键位: 高 {key_levels['recent_high']}, 低 {key_levels['recent_low']}"""

    return {
        "symbol": symbol,
        "status": "success",
        "latest_price": latest["close"],
        "price_change": price_chg,
        "volume_oi": vol_oi,
        "atr": atr,
        "ma20": ma20,
        "key_levels": key_levels,
        "observation_text": text.strip()
    }


def get_latest_observation(symbol: str, period: str = "D", lookback: int = 5) -> str:
    result = get_structured_observation(symbol, period, lookback)
    return result.get("observation_text", "获取失败")
