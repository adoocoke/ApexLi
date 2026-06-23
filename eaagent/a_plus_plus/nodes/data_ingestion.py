from datetime import datetime
import os
import re

from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.data_provider import get_market_data
from eaagent.data_providers.factory import get_data_provider


def _is_futures_symbol(symbol: str) -> bool:
    """简单判断是否为期货品种代码"""
    # 常见期货后缀
    if any(suffix in symbol.upper() for suffix in [".SHF", ".DCE", ".CZC", ".INE"]):
        return True
    # 典型期货代码格式：字母+4位数字（如 RB2605）
    if re.match(r"^[A-Za-z]{1,2}\d{4}$", symbol):
        return True
    return False


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"

    if use_mock:
        # Mock 模式：使用原有 get_market_data 逻辑
        state["market_data"] = get_market_data(
            state["data_source"], state["current_symbol"], state["timeframes"]
        )
        return state

    # 真实模式：根据品种自动选择 Provider
    provider_name = "tushare_futures" if _is_futures_symbol(state["current_symbol"]) else "tushare_stock"

    try:
        provider = get_data_provider(provider_name)
        start_date = "20240101"
        end_date = datetime.now().strftime("%Y%m%d")
        df = provider.get_daily(state["current_symbol"], start_date, end_date)

        if df is not None and not df.empty:
            latest = float(df["close"].iloc[-1]) if "close" in df.columns else None
            prev = float(df["close"].iloc[-2]) if len(df) > 1 and "close" in df.columns else None
            change_pct = round((latest - prev) / prev * 100, 2) if prev else None

            vol_trend = "unknown"
            if "vol" in df.columns and len(df) > 1:
                vol_trend = "increasing" if df["vol"].iloc[-1] > df["vol"].iloc[-2] else "decreasing"

            summary = {
                "latest_price": latest,
                "price_change_pct": change_pct,
                "volume_trend": vol_trend,
                "data_source": provider_name,
                "data_available": True,
                "rows": len(df)
            }
            state.setdefault("market_data", {})["daily_summary"] = summary
        else:
            state.setdefault("market_data", {})["daily_summary"] = {
                "data_source": provider_name,
                "data_available": False
            }
    except Exception:
        state.setdefault("market_data", {})["daily_summary"] = {
            "data_source": provider_name,
            "data_available": False
        }

    return state
