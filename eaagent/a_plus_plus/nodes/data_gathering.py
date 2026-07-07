from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.tools.tushare_futures import get_related_futures_daily, get_futures_daily_with_ma


def extract_ts_code(display_value):
    """Robust parser for Chinese '品种 代码' or '代码 代码' (fix for SA2609 SA2609.ZCE / RB2610 RB2610.SHF).
    Duplicated here (minimal) to avoid circular import with web/app_graph.py."""
    if not isinstance(display_value, str):
        return display_value
    # Handle duplicate symbols like "RB2610 RB2610.SHF" - take last valid ts_code with .
    parts = display_value.strip().split()
    for p in reversed(parts):
        if '.' in p or (any(c.isdigit() for c in p) and len(p) > 3):  # Prefer full ts_code with exchange suffix
            return p
    return display_value  # fallback

# Move RELATED_MAP here for core EA (avoid web import in nodes)
RELATED_MAP = {
    "RB": ["I2609.DCE", "JM2609.DCE"], "I": ["J2609.DCE", "JM2609.DCE"],
    "JM": ["J2609.DCE", "RB2610.SHF"], "J": ["JM2609.DCE", "I2609.DCE"],
    "SA": ["FG2606.ZCE", "SH2609.ZCE", "SA2609.ZCE"], "FG": ["SA609.ZCE", "TA1001.ZCE", "SA2609.ZCE"],  # SA2609.ZCE as requested + other active ZCE
    "AL": ["AG2609.SHF"], "AG": ["AL2610.SHF"],
    "P": ["RM2609.CZC"], "CF": ["SR2609.CZC"],
    "LC": ["AL2610.SHF"], "IC": ["IM2509.CFE"], "IM": ["IC2509.CFE"],
    "SH": ["SA609.ZCE", "SA2609.ZCE"], "TA": ["FG2606.ZCE", "SA2609.ZCE"],  # SA2609.ZCE included for all CZCE related
}

def get_related_for_symbol(symbol: str):
    """Core dynamic related for EA (0-2 per main contract)"""
    prefix = symbol.split(".")[0][:2] if "." in symbol else symbol[:2]
    return RELATED_MAP.get(prefix, ["I2609.DCE", "J2609.DCE"][:2])


def data_gathering(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 数据补充获取 (Data Gathering)", Colors.OKCYAN)

    data_requests = state.get("observations", [])[-1].get("data_requests", [])

    if "extra_data" not in state:
        state["extra_data"] = {}

    # 专心调prompt的信号：移除自动工具兜底（LLM在observation/signal_generation prompt中已明确工具调用优先，visual_analyzer优先）。extra_data仅由LLM data_requests填充。
    if not data_requests:
        color_print("  → LLM未请求额外工具 (prompt专注signals生成，visual+Playbook优先)", Colors.OKCYAN)

    for req in data_requests:
        if isinstance(req, str):
            color_print(f"  → LLM 返回字符串: {req}", Colors.WARNING)
            continue
        if not isinstance(req, dict):
            continue

        data_type = req.get("data_type", "").lower()
        reason = req.get("reason", "")
        priority = req.get("priority", "medium")

        color_print(f"  → 处理请求: {data_type} | 优先级: {priority}", Colors.OKBLUE)
        if reason:
            color_print(f"    原因: {reason}", Colors.OKCYAN)

        # Phase 3: 支持 longer_history 请求 (自动增量到12个月)
        if any(k in data_type for k in ["longer_history", "12个月", "long", "history"]) or req.get("months", 0) >= 12 or "12" in str(req):
            color_print("  → LLM 请求更长历史 (12个月)，更新 market_data 用于高质量 signal", Colors.WARNING)
            try:
                from eaagent.tools.tushare_futures import get_futures_daily_recent
                df_long = get_futures_daily_recent(state["current_symbol"], months=12)
                if not df_long.empty:
                    state["market_data"]["daily_df"] = df_long.to_dict(orient="records")
                    state["market_data"]["months_used"] = 12
                    state["market_data"]["data_available"] = True
                    color_print(f"    → 已增量获取12个月数据 ({len(df_long)} 条)，LLM 将基于此生成单笔高置信 signal", Colors.OKGREEN)
            except Exception as e:
                color_print(f"    → 增量历史失败: {e}", Colors.FAIL)

        if data_type == "相关品种日线" or "related" in data_type.lower():
            symbols = req.get("symbols", [])
            if not symbols:
                symbols = get_related_for_symbol(state.get("current_symbol", "RB2610.SHF"))
            df = get_related_futures_daily(symbols, months=3)
            state["extra_data"]["related_futures"] = df.to_dict("records") if not df.empty else []
            color_print(f"    → 已获取相关品种数据 {len(state['extra_data'].get('related_futures', []))} 条 for {state.get('current_symbol')} (symbols: {symbols})", Colors.OKGREEN)

        elif data_type == "技术指标" or "technical" in data_type.lower():
            indicators = req.get("indicators", ["volume", "oi"])  # 严格Playbook (量仓为主, 无MA13/均线)
            ma_periods = [int(''.join(filter(str.isdigit, x))) for x in indicators if any(c.isdigit() for c in x)]
            df = get_futures_daily_with_ma(state["current_symbol"], months=3, ma_periods=ma_periods or [5, 13, 20])
            state["extra_data"]["technical_indicators"] = df.to_dict("records") if not df.empty else []
            color_print(f"    → 已获取技术指标数据 {len(state['extra_data'].get('technical_indicators', []))} 条", Colors.OKGREEN)

        elif "holding" in data_type.lower():
            from .tools import get_futures_holding
            holding_result = get_futures_holding(state.get("current_symbol", "RB2610.SHF"))
            state["extra_data"]["holding"] = holding_result
            color_print(f"    → 已获取持仓数据 (status: {holding_result.get('status', 'unknown')})", Colors.OKGREEN)
            # 同时存news（如果LLM请求holding，常伴随新闻需求）
            if "news" not in state:
                news_result = get_futures_news(state.get("current_symbol", "RB2610.SHF"), limit=5)
                state["news"] = news_result.get("news", [])

        elif "news" in data_type.lower() or "新闻" in data_type.lower():
            from eaagent.a_plus_plus.tools import get_futures_news
            news_result = get_futures_news(state.get("current_symbol", "RB2610.SHF"), limit=5)
            state["news"] = news_result.get("news", [])
            state["extra_data"]["news"] = news_result
            color_print(f"    → 已获取新闻数据: {news_result.get('summary', '5条新闻')}", Colors.OKGREEN)

    color_print(f"  → extra_data 已填充: {list(state['extra_data'].keys())}", Colors.OKGREEN)
    return state
