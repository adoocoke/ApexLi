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
        # 提供少量 mock 日线数据，避免 observation 解析问题
        state["market_data"] = {
            "data_source": "MOCK",
            "daily_df": [
                {"trade_date": "2026-06-01", "open": 3200, "high": 3250, "low": 3180, "close": 3230, "vol": 120000, "oi": 45000},
                {"trade_date": "2026-06-02", "open": 3230, "high": 3280, "low": 3210, "close": 3260, "vol": 135000, "oi": 46000},
                {"trade_date": "2026-06-03", "open": 3260, "high": 3300, "low": 3240, "close": 3275, "vol": 110000, "oi": 45500},
            ],
            "data_available": True
        }
    else:
        # Phase 3 优化: 优先5个月数据，如果不足(~80根K线)自动增量到12个月
        months = 5
        color_print(f"  → 使用 Tushare 获取 {symbol} 最近{months}个月日线数据", Colors.OKBLUE)
        try:
            df = get_futures_daily_recent(symbol, months=months)
            if df.empty or len(df) < 80:  # 5个月通常 >80根，数据不足则增量
                color_print(f"  → 5个月数据不足 ({len(df)}条)，自动增量到12个月", Colors.WARNING)
                df = get_futures_daily_recent(symbol, months=12)
            
            if not df.empty:
                color_print(f"  → 成功获取 {len(df)} 条日线数据 (用于 LLM 生成高质量 signal)", Colors.OKGREEN)
                state["market_data"] = {
                    "data_source": "TUSHARE",
                    "daily_df": df.to_dict(orient="records"),
                    "data_available": True,
                    "last_update": df['trade_date'].iloc[-1] if len(df) > 0 else None,
                    "months_used": 12 if len(df) > 150 else 5
                }
            else:
                color_print("  → Tushare 返回空数据，使用 Mock fallback", Colors.WARNING)
                state["market_data"] = {
                    "data_source": "TUSHARE",
                    "daily_df": [],
                    "data_available": False
                }
        except Exception as e:
            color_print(f"  → 获取日线数据失败: {e}，使用 Mock fallback", Colors.FAIL)
            state["market_data"] = {
                "data_source": "TUSHARE",
                "daily_df": [],
                "data_available": False
            }

    return state
