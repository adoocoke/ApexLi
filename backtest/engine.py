"""
Phase 3: VectorBT 回测引擎 (最小实现)
支持单品种回测，生成资金曲线 + 核心指标 (Sharpe, MaxDD, WinRate)。
复用现有 tushare_futures + EA 信号 (后续从 graph signals 集成)。
"""

import vectorbt as vbt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any
import os

def run_backtest(symbol: str = "RB2610.SHF", months: int = 12, initial_capital: float = 100000.0) -> Dict[str, Any]:
    """最小 VectorBT 回测引擎 (单品种)
    - 从 tushare 获取数据
    - 简单移动平均信号 (后续替换为 EA graph 信号)
    - 输出资金曲线 + 指标
    """
    try:
        from eaagent.tools.tushare_futures import get_futures_daily_with_ma
        df = get_futures_daily_with_ma(symbol, months=months)
        if df.empty:
            return {"status": "error", "reason": "No data", "equity": pd.Series()}

        # 简单信号 (MA crossover) - 后续替换为 EA 信号
        price = df["close"]
        fast_ma = price.rolling(10).mean()
        slow_ma = price.rolling(30).mean()
        entries = fast_ma.vbt.crossed_above(slow_ma)
        exits = fast_ma.vbt.crossed_below(slow_ma)

        # VectorBT Portfolio
        pf = vbt.Portfolio.from_signals(
            price,
            entries=entries,
            exits=exits,
            init_cash=initial_capital,
            fees=0.001,
            freq="1D"
        )

        equity = pf.equity()
        stats = pf.stats()

        return {
            "status": "success",
            "symbol": symbol,
            "equity": equity,
            "stats": {
                "sharpe_ratio": float(stats.get("Sharpe Ratio", 0.0)),
                "max_drawdown": float(stats.get("Max Drawdown", 0.0)),
                "win_rate": float(stats.get("Win Rate", 0.0)),
                "total_return": float(stats.get("Total Return", 0.0)),
                "trades": int(stats.get("Total Trades", 0)),
            },
            "pf": pf  # 用于 Dashboard 可视化
        }
    except Exception as e:
        return {"status": "error", "reason": str(e), "equity": pd.Series()}


def batch_backtest(symbols: list = None, months: int = 6) -> Dict[str, Any]:
    """多品种批量回测 (Phase 3 扩展)"""
    if symbols is None:
        symbols = ["RB2610.SHF", "I2609.DCE", "SA2609.ZCE"]
    results = {}
    for sym in symbols:
        results[sym] = run_backtest(sym, months=months)
    return results


if __name__ == "__main__":
    result = run_backtest("RB2610.SHF")
    print("✅ Backtest completed")
    print("Stats:", result["stats"])
    print("Equity shape:", len(result["equity"]) if not result["equity"].empty else 0)
