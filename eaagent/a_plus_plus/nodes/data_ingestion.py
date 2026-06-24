from datetime import datetime
import os
from eaagent.a_plus_plus.types import TAState
from eaagent.tools.tushare_futures import get_futures_daily_recent
from eaagent.a_plus_plus.data_provider import get_market_data

def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"

    if not use_mock:
        try:
            # 使用 5 个月数据
            df = get_futures_daily_recent(state["current_symbol"], months=5)
            if df is not None and not df.empty:
                state.setdefault("market_data", {})["daily_df"] = df.to_dict(orient="records")
                state["market_data"]["data_source"] = "TUSHARE"
                state["market_data"]["data_available"] = True
                state["market_data"]["last_update"] = datetime.now().isoformat()
                print(f"[Data] 使用 Tushare 获取 {state['current_symbol']} 最近5个月日线数据")
                print(f"[Data] 成功获取 {len(df)} 条日线数据")
                return state
        except Exception as e:
            print(f"[Data] Tushare 获取失败: {e}")

    # Mock 模式或降级
    state["market_data"] = get_market_data(
        state.get("data_source", "mock"),
        state["current_symbol"],
        state.get("timeframes", ["5m", "30m", "1d"])
    )
    return state
