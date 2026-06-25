from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.tools.tushare_futures import get_futures_daily_recent
import os


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    color_print(f"\n[第 {state['iteration']} 轮] 数据获取阶段", Colors.OKCYAN)

    symbol = state["current_symbol"]

    # 强制只使用日线数据（推荐做法）
    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"

    if use_mock:
        color_print("  → 使用 Mock 数据", Colors.WARNING)
        state["market_data"] = {
            "data_source": "MOCK",
            "daily_df": [],  # 这里可以放 mock 日线数据
            "data_available": False
        }
    else:
        color_print(f"  → 使用 Tushare 获取 {symbol} 最近5个月日线数据", Colors.OKBLUE)
        try:
            df = get_futures_daily_recent(symbol, months=5)
            if not df.empty:
                color_print(f"  → 成功获取 {len(df)} 条日线数据", Colors.OKGREEN)
                state["market_data"] = {
                    "data_source": "TUSHARE",
                    "daily_df": df.to_dict(orient="records"),
                    "data_available": True,
                    "last_update": df['trade_date'].iloc[-1] if len(df) > 0 else None
                }
            else:
                color_print("  → Tushare 返回空数据", Colors.WARNING)
                state["market_data"] = {
                    "data_source": "TUSHARE",
                    "daily_df": [],
                    "data_available": False
                }
        except Exception as e:
            color_print(f"  → 获取日线数据失败: {e}", Colors.FAIL)
            state["market_data"] = {
                "data_source": "TUSHARE",
                "daily_df": [],
                "data_available": False
            }

    return state
