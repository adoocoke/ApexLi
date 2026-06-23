from datetime import datetime
import os

from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.data_provider import get_market_data
from eaagent.data_providers.factory import get_data_provider


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"
    if not use_mock:
        try:
            provider = get_data_provider("tushare_futures")
            start_date = "20240101"
            end_date = datetime.now().strftime("%Y%m%d")
            df = provider.get_daily(state["current_symbol"], start_date, end_date)
            if df is not None and not df.empty:
                summary = {
                    "latest_close": float(df["close"].iloc[-1]) if "close" in df.columns else None,
                    "latest_date": str(df["trade_date"].iloc[-1]) if "trade_date" in df.columns else None,
                    "last_5_closes": df["close"].tail(5).tolist() if "close" in df.columns else [],
                    "volume_trend": (
                        "increasing" if len(df) > 1 and df["vol"].iloc[-1] > df["vol"].iloc[-2]
                        else "decreasing" if "vol" in df.columns else "unknown"
                    ),
                    "rows": len(df)
                }
                state.setdefault("market_data", {})["daily_summary"] = summary
        except Exception:
            pass  # fallback to old logic below

    # Fallback / original behavior (kept for mock mode and error cases)
    if "daily_summary" not in state.get("market_data", {}):
        state["market_data"] = get_market_data(
            state["data_source"], state["current_symbol"], state["timeframes"]
        )
    return state
