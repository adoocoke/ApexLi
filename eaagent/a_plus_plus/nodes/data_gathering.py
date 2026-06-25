from eaagent.a_plus_plus.types import TAState
from eaagent.tools.tushare_futures import (
    get_related_futures_daily,
    get_futures_daily_with_ma
)
from eaagent.a_plus_plus.utils.console import color_print, Colors


def data_gathering(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 数据补充获取 (Data Gathering)", Colors.OKGREEN)

    observations = state.get("observations", [])
    if not observations:
        if "extra_data" not in state:
            state["extra_data"] = {}
        return state

    latest_obs = observations[-1]
    data_requests = latest_obs.get("data_requests", [])

    if not data_requests:
        print("[Data Gathering] 本轮无额外数据请求")
        if "extra_data" not in state:
            state["extra_data"] = {}
        return state

    if "extra_data" not in state:
        state["extra_data"] = {}

    for req in data_requests:
        data_type = req.get("data_type", "")
        reason = req.get("reason", "")
        priority = req.get("priority", "medium")

        print(f"[Data Gathering] 处理请求: {data_type} | 优先级: {priority}")
        print(f"  原因: {reason}")

        try:
            if data_type == "相关品种日线":
                symbols = req.get("symbols", [])
                if symbols:
                    df = get_related_futures_daily(symbols, months=3)
                    state["extra_data"]["related_futures"] = df.to_dict(orient="records") if not df.empty else []
                    print(f"  → 已获取相关品种数据: {symbols}")

            elif data_type == "技术指标":
                indicators = req.get("indicators", ["MA5", "MA13", "MA20"])
                ma_periods = []
                for x in indicators:
                    if isinstance(x, str) and x.upper().startswith("MA") and x.upper() != "MACD":
                        try:
                            period = int(''.join(filter(str.isdigit, x)))
                            if period > 0:
                                ma_periods.append(period)
                        except:
                            pass

                if ma_periods:
                    df = get_futures_daily_with_ma(
                        state["current_symbol"],
                        months=3,
                        ma_periods=ma_periods
                    )
                    state["extra_data"]["technical_indicators"] = df.to_dict(orient="records") if not df.empty else []
                    print(f"  → 已获取技术指标数据，均线周期: {ma_periods}")
                else:
                    print("  → 未识别到有效的均线周期，跳过")

        except Exception as e:
            print(f"  [Data Gathering] 处理 {data_type} 时出错: {e}")

    return state
