from eaagent.a_plus_plus.types import TAState
from eaagent.tools.tushare_futures import (
    get_related_futures_daily,
    get_futures_daily_with_ma
)
from eaagent.a_plus_plus.utils.console import color_print, Colors
from typing import Any

def data_gathering(state: TAState) -> dict:
    color_print(f"[第 {state.get('iteration', 0)} 轮] 数据补充获取 (Data Gathering)", Colors.OKGREEN)

    observations = state.get("observations", [])
    if not observations:
        return {}

    latest_obs = observations[-1]
    data_requests = latest_obs.get("data_requests", [])

    if not data_requests:
        return {}

    # 使用 reducer 后的 extra_data
    extra_data: Dict[str, Any] = state.get("extra_data", {}) or {}
    history = state.get("extra_data_history", [])

    for req in data_requests:
        data_type = req.get("data_type", "")
        reason = req.get("reason", "")
        priority = req.get("priority", "medium")

        print(f"[Data Gathering] 处理请求: {data_type} | 优先级: {priority}")

        try:
            if data_type == "相关品种日线":
                symbols = req.get("symbols", [])
                if symbols:
                    df = get_related_futures_daily(symbols, months=3)
                    print(f"  [DEBUG] related_futures df shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
                    print(f"  [DEBUG] related_futures df empty: {df.empty if hasattr(df, 'empty') else 'N/A'}")
                    print(f"  [DEBUG] related_futures columns: {list(df.columns) if not df.empty else 'empty'}")

                    extra_data["related_futures"] = df.to_dict(orient="records") if not df.empty else []
                    print(f"  → 已获取相关品种数据: {symbols}")

            elif data_type == "技术指标":
                indicators = req.get("indicators", ["MA5", "MA13", "MA20"])
                ma_periods = []
                for x in indicators:
                    if isinstance(x, str) and x.upper().startswith("MA") and x.upper() != "MACD":
                        digits = ''.join(filter(str.isdigit, x))
                        if digits:
                            try:
                                period = int(digits)
                                if period > 0:
                                    ma_periods.append(period)
                            except ValueError:
                                continue

                if ma_periods:
                    df = get_futures_daily_with_ma(
                        state["current_symbol"],
                        months=3,
                        ma_periods=sorted(set(ma_periods))
                    )
                    extra_data["technical_indicators"] = df.to_dict(orient="records") if not df.empty else []
                    print(f"  → 已获取技术指标数据，均线周期: {sorted(set(ma_periods))}")

        except Exception as e:
            print(f"  [Data Gathering] 处理 {data_type} 时出错: {e}")

    print(f"[DEBUG] data_gathering 准备返回 extra_data keys: {list(extra_data.keys())}")
    print(f"[DEBUG] extra_data 内容预览: { {k: len(v) if isinstance(v, list) else 'dict' for k,v in extra_data.items()} }")
    # 关键：只返回需要更新的部分
    # 返回更新（reducer 会自动合并）
    update = {"extra_data": extra_data}
    if history is not None:
        update["extra_data_history"] = history + [{"round": state.get("iteration"), "data": extra_data}]

    return update