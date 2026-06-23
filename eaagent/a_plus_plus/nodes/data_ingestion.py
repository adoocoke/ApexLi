from datetime import datetime
import os

from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.data_provider import get_market_data
from eaagent.data_providers.factory import get_data_provider


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"

    if use_mock:
        # Mock 模式：使用原有 get_market_data 逻辑
        state["market_data"] = get_market_data(
            state["data_source"], state["current_symbol"], state["timeframes"]
        )
    else:
        # 真实模式：使用新 DataProvider，只存摘要（避免 DataFrame 序列化问题）
        try:
            provider = get_data_provider("tushare_futures")
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
                    "data_available": True,
                    "rows": len(df)
                }
                state.setdefault("market_data", {})["daily_summary"] = summary
            else:
                state.setdefault("market_data", {})["daily_summary"] = {"data_available": False}
        except Exception:
            state.setdefault("market_data", {})["daily_summary"] = {"data_available": False}

    return state
