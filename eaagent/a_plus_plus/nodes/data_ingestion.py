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

        market_data = {
            "data_source": provider_name,
            "data_available": False,
            "last_update": datetime.now().isoformat()
        }

        # 日线
        df_daily = provider.get_daily(state["current_symbol"], start_date, end_date)
        if df_daily is not None and not df_daily.empty:
            latest = float(df_daily["close"].iloc[-1]) if "close" in df_daily.columns else None
            prev = float(df_daily["close"].iloc[-2]) if len(df_daily) > 1 and "close" in df_daily.columns else None
            change_pct = round((latest - prev) / prev * 100, 2) if prev else None
            vol_trend = "unknown"
            if "vol" in df_daily.columns and len(df_daily) > 1:
                vol_trend = "increasing" if df_daily["vol"].iloc[-1] > df_daily["vol"].iloc[-2] else "decreasing"

            market_data.update({
                "daily_latest_price": latest,
                "daily_change_pct": change_pct,
                "daily_volume_trend": vol_trend,
                "data_available": True
            })

        # 30分钟
        df_30m = provider.get_minute(state["current_symbol"], start_date, end_date, freq="30min")
        if df_30m is not None and not df_30m.empty:
            latest = float(df_30m["close"].iloc[-1]) if "close" in df_30m.columns else None
            prev = float(df_30m["close"].iloc[-2]) if len(df_30m) > 1 and "close" in df_30m.columns else None
            change_pct = round((latest - prev) / prev * 100, 2) if prev else None
            market_data.update({
                "30m_latest_price": latest,
                "30m_change_pct": change_pct,
                "data_available": True
            })

        # 3分钟
        df_3m = provider.get_minute(state["current_symbol"], start_date, end_date, freq="3min")
        if df_3m is not None and not df_3m.empty:
            latest = float(df_3m["close"].iloc[-1]) if "close" in df_3m.columns else None
            prev = float(df_3m["close"].iloc[-2]) if len(df_3m) > 1 and "close" in df_3m.columns else None
            change_pct = round((latest - prev) / prev * 100, 2) if prev else None
            market_data.update({
                "3m_latest_price": latest,
                "3m_change_pct": change_pct,
                "data_available": True
            })

        state["market_data"] = market_data

    except Exception:
        state["market_data"] = {
            "data_source": provider_name,
            "data_available": False,
            "last_update": datetime.now().isoformat()
        }

    return state
