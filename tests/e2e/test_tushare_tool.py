"""
Tushare 工具单元测试（A计划 - 20260605）
测试数据格式化逻辑，不依赖真实 API
"""

import pandas as pd
import pytest

from eaagent.tools.tushare_futures import _format_futures_summary


def test_format_futures_summary_basic():
    """ 测试基础格式化功能 """
    data = {
        "trade_date": ["20240301", "20240304", "20240305"],
        "open": [3760.0, 3765.0, 3750.0],
        "high": [3770.0, 3775.0, 3760.0],
        "low": [3755.0, 3750.0, 3720.0],
        "close": [3763.0, 3762.0, 3723.0],
        "vol": [120000, 135000, 98000],
        "oi": [850000, 860000, 870000],
    }
    df = pd.DataFrame(data)

    result = _format_futures_summary(df, "RB2405.SHF")

    assert "RB2405.SHF" in result
    assert "最新收盘: 3723.00" in result
    assert "区间最高: 3775.00" in result
    assert "最近交易日数据" in result
    assert "20240305" in result


def test_format_futures_summary_empty():
    """ 测试空数据情况 """
    df = pd.DataFrame()
    result = _format_futures_summary(df, "RB2405.SHF")
    assert "未查询到" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
