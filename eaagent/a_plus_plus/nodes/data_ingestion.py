from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.data_provider import get_market_data


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")
    state["market_data"] = get_market_data(
        state["data_source"], state["current_symbol"], state["timeframes"]
    )
    return state
