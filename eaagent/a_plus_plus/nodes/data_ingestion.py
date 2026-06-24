from datetime import datetime
import os
from eaagent.a_plus_plus.types import TAState
from eaagent.tools.tushare_futures import get_futures_daily_recent


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    symbol = state["current_symbol"]

    # 判断是否为期货品种
    is_futures = any(x in symbol.upper() for x in [".SHF", ".DCE", ".CZC", ".INE"])

    if is_futures:
        print(f"[Data] 使用 Tushare 获取 {symbol} 最近3个月日线数据")
        try:
            df = get_futures_daily_recent(ts_code=symbol, months=3)
            if df is not None and not df.empty:
                state["market_data"] = {
                    "daily_df": df,
                    "data_source": "tushare_futures",
                    "data_available": True,
                    "last_update": datetime.now().isoformat()
                }
                print(f"[Data] 成功获取 {len(df)} 条日线数据")
            else:
                state["market_data"] = {
                    "data_source": "tushare_futures",
                    "data_available": False,
                    "last_update": datetime.now().isoformat()
                }
                print("[Data] 获取数据为空")
        except Exception as e:
            print(f"[Data] 获取 Tushare 数据失败: {e}")
            state["market_data"] = {
                "data_source": "tushare_futures",
                "data_available": False,
                "last_update": datetime.now().isoformat()
            }
    else:
        print(f"[Data] 当前品种 {symbol} 非期货，暂不自动获取数据")
        state["market_data"] = {
            "data_available": False,
            "last_update": datetime.now().isoformat()
        }

    return state
