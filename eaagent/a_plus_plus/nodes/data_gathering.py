from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.tools.tushare_futures import get_related_futures_daily, get_futures_daily_with_ma

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

    for req in data_requests:
        if isinstance(req, str):
            color_print(f"  → LLM 返回字符串: {req}", Colors.WARNING)
            continue
        if not isinstance(req, dict):
            continue

        data_type = req.get("data_type", "")
        reason = req.get("reason", "")
        priority = req.get("priority", "medium")

        color_print(f"  → 处理请求: {data_type} | 优先级: {priority}", Colors.OKBLUE)
        if reason:
            color_print(f"    原因: {reason}", Colors.OKCYAN)

        if data_type == "相关品种日线":
            # Fully dynamic per current_symbol (no fixed fallback)
            symbols = req.get("symbols", [])
            if not symbols:  # LLM didn't provide or empty → use map
                symbols = get_related_for_symbol(state.get("current_symbol", "RB2610.SHF"))
            df = get_related_futures_daily(symbols, months=3)
            state["extra_data"]["related_futures"] = df.to_dict("records") if not df.empty else []
            color_print(f"    → 已获取相关品种数据 {len(state['extra_data'].get('related_futures', []))} 条 for {state.get('current_symbol')} (symbols: {symbols})", Colors.OKGREEN)

        elif data_type == "技术指标":
            indicators = req.get("indicators", ["MA5", "MA13", "MA20"])
            ma_periods = [int(''.join(filter(str.isdigit, x))) for x in indicators if any(c.isdigit() for c in x)]
            df = get_futures_daily_with_ma(state["current_symbol"], months=3, ma_periods=ma_periods or [5, 13, 20])
            state["extra_data"]["technical_indicators"] = df.to_dict("records") if not df.empty else []
            color_print(f"    → 已获取技术指标数据 {len(state['extra_data'].get('technical_indicators', []))} 条", Colors.OKGREEN)

    color_print(f"  → extra_data 已填充: {list(state['extra_data'].keys())}", Colors.OKGREEN)
    return state
