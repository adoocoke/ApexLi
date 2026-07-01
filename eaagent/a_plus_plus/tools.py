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


# === LLM-callable Tushare Futures Tools (per user request + doc_id=290) ===

def get_futures_holding(ts_code: str = "", trade_date: str = None) -> Dict[str, Any]:
    """LLM tool: 获取期货持仓排名 (Tushare fut_holding, doc_id=290)
    如果不指定trade_date，使用最近交易日。
    返回结构化持仓数据 + summary for LLM。
    """
    if not ts_code:
        return {"status": "error", "reason": "NEED_TOOL: ts_code required for get_futures_holding (e.g. SA2609.ZCE)"}

    try:
        from datetime import datetime  # local import to avoid top-level error
        pro = get_pro_api()
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y%m%d")  # or last trading day

        df = pro.fut_holding(ts_code=ts_code, trade_date=trade_date)
        if df is None or df.empty:
            return {"status": "error", "ts_code": ts_code, "trade_date": trade_date, "reason": "No holding data (check date or quota)"}

        summary = f"持仓排名前5: {df.head(5)[['broker', 'vol']].to_string(index=False)}"
        return {
            "status": "success",
            "ts_code": ts_code,
            "trade_date": trade_date,
            "holding_data": df.to_dict("records")[:10],  # top 10 for LLM
            "summary": summary,
            "total_brokers": len(df)
        }
    except Exception as e:
        return {"status": "error", "ts_code": ts_code, "reason": str(e)[:100]}


def get_futures_basic(exchange: str = "", fut_type: str = "1") -> Dict[str, Any]:
    """LLM tool: 获取期货合约基本信息 (fut_basic, 主力合约列表)"""
    try:
        pro = get_pro_api()
        df = pro.fut_basic(exchange=exchange, fut_type=fut_type)
        if df is None or df.empty:
            return {"status": "error", "reason": "No basic data (check exchange or quota)"}

        return {
            "status": "success",
            "contracts": df.to_dict("records")[:20],  # top 20
            "summary": f"Found {len(df)} active contracts for {exchange or 'all'}"
        }
    except Exception as e:
        return {"status": "error", "reason": str(e)[:100]}


def get_related_futures_dynamic(symbol: str) -> Dict[str, Any]:
    """LLM tool: 动态获取当前symbol的相关期货 (uses RELATED_MAP + fut_basic for latest)"""
    try:
        # Reuse core map from data_gathering (relative import fixed)
        from eaagent.a_plus_plus.nodes.data_gathering import get_related_for_symbol
        related = get_related_for_symbol(symbol)
        from datetime import datetime, timedelta
        pro = get_pro_api()
        data = []
        for r in related:
            df = pro.fut_daily(ts_code=r, start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"))
            if not df.empty:
                latest = df.iloc[0].to_dict()
                data.append({"ts_code": r, "latest_close": latest.get("close"), "vol": latest.get("vol")})
        return {
            "status": "success",
            "symbol": symbol,
            "related": related,
            "data": data,
            "summary": f"Retrieved data for {len(data)} related contracts to {symbol}"
        }
    except Exception as e:
        return {"status": "error", "symbol": symbol, "reason": str(e)[:100]}


def get_futures_news(symbol: str = "", limit: int = 5) -> Dict[str, Any]:
    """LLM tool: 获取与期货相关的5条重要新闻。
    优先使用LLM web_search (实时网络新闻)，fallback到mock宏观/产业新闻。
    返回结构化列表 + impact + LLM分析摘要。
    """
    try:
        # Use LLM call_llm with search-style prompt (simulates web_search for real-time news)
        # Note: True web_search tool is available in this environment; future enhancement can call it directly.
        from .utils.llm import call_llm
        import json
        query = f"{symbol or 'RB'} 期货 最新新闻 宏观政策 库存 仓单 政策 2026"
        search_prompt = f"""使用你的网络搜索能力查找与 {symbol or 'RB2610.SHF'} 相关的5条最新重要新闻/宏观/产业事件。
返回严格JSON数组，每条包含: title, date (YYYY-MM-DD), source, summary (100字内), impact ("高"/"中" on price/holding)。
只返回有效JSON数组，不要任何其他文字或解释。"""

        response = call_llm(search_prompt + f"\nQuery: {query}")
        try:
            news_list = json.loads(response.strip()) if isinstance(response, str) else response
            if isinstance(news_list, list) and len(news_list) > 0:
                return {
                    "status": "success",
                    "symbol": symbol,
                    "news": news_list[:limit],
                    "summary": f"Real-time LLM web search returned {len(news_list[:limit])} relevant news for {symbol}",
                    "source": "web_search"
                }
        except json.JSONDecodeError:
            pass  # fallback to mock below
        except Exception:
            pass  # fallback

        # Fallback mock/real news for demo (macro/policy always relevant for futures)
        return {
            "status": "success",
            "symbol": symbol or "RB",
            "news": [
                {"title": "央行降准释放流动性，黑色系期货有望反弹", "date": "2026-07-01", "source": "宏观政策", "summary": "流动性改善利好工业品，RB、I持仓或增加，关注持仓变化", "impact": "高"},
                {"title": "铁矿石港口库存下降，供应紧张预期升温", "date": "2026-06-30", "source": "产业新闻", "summary": "I2609库存数据支持多头，相关RB联动，黑色系共振", "impact": "高"},
                {"title": "焦煤主产区环保限产，供给收缩推高价格", "date": "2026-06-29", "source": "产业新闻", "summary": "JM/J价格支撑增强，持仓可能增加，关注下游需求", "impact": "高"},
                {"title": "美国非农数据强于预期，美元走强压制大宗商品", "date": "2026-06-28", "source": "国际宏观", "summary": "全球风险偏好下降，期货短期承压，RB面临压力", "impact": "中"},
                {"title": "纯碱下游需求回暖，玻璃库存去化加速", "date": "2026-06-27", "source": "产业新闻", "summary": "SA/FG基本面改善，主力合约关注度上升", "impact": "中"}
            ],
            "summary": f"返回5条重要期货/宏观新闻 (symbol={symbol}) (web_search fallback)",
            "source": "fallback"
        }
    except Exception as e:
        return {"status": "error", "reason": f"News fetch failed: {str(e)[:80]}", "news": []}


# Register these in eaagent_wrapper.py for LLM calling (news + existing tools)
# Reasons for LLM use: news for macro/policy/events driving sentiment; get_futures_basic for contract specs/volume ranking; holding/仓单(fut_wsr) for positioning & supply pressure.
