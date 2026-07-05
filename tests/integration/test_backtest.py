"""
Phase 3 Test-First: VectorBT 回测引擎测试 (backtest/engine.py)
测试资金曲线生成、指标计算 (Sharpe, MaxDD, WinRate)、单/多品种支持。
复用现有 tushare_futures 数据。
"""

import pytest
import pandas as pd
from pathlib import Path

# TODO: 实现后取消 skip
@pytest.mark.skip("Phase 3 backtest 实现后启用")
def test_vectorbt_single_symbol_backtest():
    """单品种回测：生成资金曲线 + 核心指标"""
    # 模拟数据 (复用 mock_data/rb2605_fut_daily_2025.csv)
    df = pd.read_csv("artifacts/mock_data/rb2605_fut_daily_2025.csv", parse_dates=["trade_date"])
    df = df.set_index("trade_date")
    
    # 简单信号 (后续从 EA graph 信号生成)
    df["signal"] = 1  # 1 = long, -1 = short, 0 = flat
    
    # VectorBT 回测 (最小实现)
    # portfolio = vbt.Portfolio.from_signals(...) 
    # equity = portfolio.equity()
    # metrics = portfolio.stats()
    
    assert not df.empty
    assert "close" in df.columns
    # assert equity is not None
    # assert "Sharpe Ratio" in metrics
    # assert "Max Drawdown" in metrics
    print("✅ VectorBT 单品种回测测试通过 (骨架)")


@pytest.mark.skip("Phase 3 backtest 实现后启用")
def test_backtest_multi_symbol_batch():
    """多品种批量回测"""
    symbols = ["RB2610.SHF", "I2609.DCE", "SA2609.ZCE"]
    results = {}
    for sym in symbols:
        # 模拟每个品种回测结果
        results[sym] = {"sharpe": 1.2, "max_dd": -0.15, "win_rate": 0.65}
    
    assert len(results) == 3
    assert all("sharpe" in v for v in results.values())
    print("✅ 多品种批量回测测试通过 (骨架)")


if __name__ == "__main__":
    test_vectorbt_single_symbol_backtest()
    test_backtest_multi_symbol_batch()
    print("=== Phase 3 backtest tests completed ===")
