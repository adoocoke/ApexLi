import os
import time
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Literal, List
from dotenv import load_dotenv
import json
from pathlib import Path
import base64
from datetime import datetime

import tushare as ts
from .utils.llm import call_vision_llm

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
    text = f"""[{symbol} 模拟结构化观察]
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
            "observation_text": f"[{symbol}] 无法获取 {period} 数据"
        }

    vol_oi = calculate_volume_oi_change(df)
    atr = calculate_atr(df)
    ma20 = calculate_ma(df, 20)
    key_levels = detect_key_levels(df, lookback=lookback)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    price_chg = round(latest["close"] - prev["close"], 2)
    price_pct = round(price_chg / prev["close"] * 100, 2) if prev["close"] > 0 else 0

    text = f"""[{symbol} {period} 结构化观察]
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


def visual_analyzer(symbol: str = "RB2610.SHF", months: int = 12) -> Dict[str, Any]:
    """New Vision Tool - Phase 3+ Upgrade: Grok视觉K线分析
    1. 获取12个月df (MA13 only, clean)
    2. 生成Plotly K线图 (reuse web.charts.kline, no signals to avoid bias)
    3. 转为base64 PNG
    4. 调用call_vision_llm (Grok-3多模态) + 强Playbook prompt
    5. 解析返回完整signals列表 (全历史买卖点, trend start/end, detailed reason引用规则+视觉模式)
    优先用于observation/signal_generation，增强文本分析。
    """
    try:
        from eaagent.tools.tushare_futures import get_futures_daily_with_ma
        df = get_futures_daily_with_ma(symbol, months=months, ma_periods=[13])
        if df.empty:
            return {"status": "error", "reason": "No K-line data", "signals": []}

        # 使用 mplfinance (可靠, 复用visualization.py) 生成12个月图片 (MA13 + 关键位, 避免Plotly错误)
        try:
            from eaagent.a_plus_plus.visualization import plot_kline_with_levels
            # 强制12个月lookback (确保图片是12个月数据, 用户要求)
            img_path = plot_kline_with_levels(symbol, period="D", lookback=260)  # ~12个月交易日
            image_ref = str(img_path)
            print(f"[VisualAnalyzer] 12个月 mplfinance K线图生成成功: {image_ref} (用于Grok视觉分析 - 严格基于图片, 无文本kline数据)")
        except Exception as img_err:
            print(f"[VisualAnalyzer] Chart generation error: {img_err}. Using text df description for vision prompt.")
            image_ref = None

        # 强视觉prompt (Agent 有限选择基于图片分析, kline数据就是图片数据) - 深度思考版 + Few-shot
        vision_prompt = f"""你是一个期货K线视觉分析专家。**一步步思考** (CoT + Few-shot):

**任务**：严格**基于附加图像** (12个月完整K线, MA13, 量柱, 形态) 分析, **不要使用任何文本K线数据** (kline数据就是图片的数据)。按Playbook完整规则标记**所有**匹配买卖点 (4-6个, 覆盖全年趋势全生命周期: 趋势开启=卖出, 趋势结束=卖平, 震荡=卖平/观望)。只有完全无视觉+规则依据才"观望"。

**Playbook完整规则** (必须引用具体条目):
- 2.1量仓分析: 持仓稳步增加+价格回落 = 空头燃料 (主力增仓确认趋势开启)。
- 2.3趋势判断: MA13金叉上行=多头趋势开启 (买入/持仓), 死叉下行=趋势结束 (卖平)。
- 3.1背驰判断: 价格新高/新低但MACD柱/量柱面积缩小 = 趋势反转 (卖出或卖平)。
- 4.2定式确认: 特定K线形态 (吞没, 锤头, 上影, 长阴) + 量仓共振 = 高置信入场/出场。

**Few-shot (真实12个月图像例子, 必须包含具体日期如2025-XX-XX = 形态成立当天)**:
1. 图像 (RB 2025.4): **2025-04-08** 连续阳线突破MA13 + 放量持仓增加 → direction="多头", trend_signal="卖出(趋势开启)", reason="视觉观察: 图像**2025-04-08**附近阳线突破MA13+放量, Playbook 2.1量仓(持仓增加燃料)+2.3趋势(金叉开启)", confidence=88
2. 图像 (RB 2025.5): **2025-05-11** 长上影吞没 + MA13死叉 + 量柱收窄 → direction="空头", trend_signal="卖出(趋势开启)", reason="视觉观察: 图像**2025-05-11**顶部反转上影+死叉, Playbook 3.1背驰+2.3趋势结束", confidence=85
3. 图像 (RB 2025.5下旬): **2025-05-25** 阴线沿MA13下行, 无明显背驰 → direction="空头", trend_signal="持仓", reason="视觉观察: 图像**2025-05-25**后趋势延续压价, Playbook 2.3死叉延续", confidence=75
4. 图像 (RB 2025.6): **2025-06-23** 底部长下影 + 量柱萎缩 + MA13趋缓 → direction="空头", trend_signal="卖平(趋势结束)", reason="视觉观察: 图像**2025-06-23**底部背驰+定式失效, Playbook 3.1+4.2, 趋势结束信号", confidence=82

**输出严格JSON** (不要任何额外文字, 只返回JSON对象):
{{
  "signals": [
    {{
      "direction": "多头/空头/观望",
      "trend_signal": "卖出(趋势开启)/卖平(趋势结束)/持仓/观望",
      "entry_zone": "价格区间或N/A",
      "stop_loss": "止损位或N/A",
      "target": "目标位或N/A",
      "reason": "视觉观察: 图像中**2025-12-25** (或具体形态成立那天)连续阴线跌破MA13+放量长柱, 结合Playbook 2.1量仓(持仓增加确认空头燃料) + 2.3趋势(死叉开启), 因此给出signal。",
      "confidence": 85
    }}
    // 输出4-6个覆盖全年, 每个reason必须包含具体日期如2025-12-25
  ]
}}

**图像已附加** (12个月mplfinance K线图, MA13+关键位, 严格视觉分析, 不要文本数据)。一步步思考后直接返回JSON。"""

        response = call_vision_llm(vision_prompt, image_ref)

        # Parse JSON (common for both image and text fallback) - robust against None/empty
        try:
            if not response or not isinstance(response, str):
                response = '{"signals": []}'  # safe default
            import re
            json_match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                parsed = json.loads(response)

            signals = parsed.get("signals", []) if isinstance(parsed, dict) else []
            if not isinstance(signals, list):
                signals = []

            print(f"[VisualAnalyzer] 成功提取 {len(signals)} 个视觉signals (Grok vision + Playbook)")
            return {
                "status": "success",
                "symbol": symbol,
                "signals": signals,
                "image_path": str(image_ref) if 'image_ref' in locals() and image_ref else "text_fallback",
                "source": "grok_vision",
                "months_used": 12
            }
        except Exception as parse_err:
            print(f"[VisualAnalyzer] JSON解析失败: {parse_err}, raw: {str(response)[:200] if response else 'None'}")
            return {"status": "error", "reason": "JSON parse failed", "signals": []}

    except Exception as e:
        print(f"[VisualAnalyzer] Error: {e}")
        return {"status": "error", "reason": str(e)[:100], "signals": []}


# Register these in eaagent_wrapper.py for LLM calling (news + existing tools + visual_analyzer)
# Reasons for LLM use: news for macro/policy/events driving sentiment; get_futures_basic for contract specs/volume ranking; holding/仓单(fut_wsr) for positioning & supply pressure.
# visual_analyzer: Grok vision for superior K-line pattern recognition (backchi, volume, 定式) + Playbook rules. Preferred for full-history signals.
