import sys
from pathlib import Path
import pandas as pd
import pytest
import plotly.graph_objects as go

# ==================== 关键：添加项目根目录到路径 ====================
project_root = Path(__file__).parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from web.charts.kline import create_candlestick_chart


def make_sample_df(n=30):
    """生成测试用K线数据"""
    dates = pd.date_range('2026-01-01', periods=n, freq='D')
    df = pd.DataFrame({
        'trade_date': dates,
        'open': 3000 + pd.Series(range(n)).cumsum() % 50,
        'high': 3050 + pd.Series(range(n)).cumsum() % 60,
        'low':  2950 + pd.Series(range(n)).cumsum() % 40,
        'close': 3000 + pd.Series(range(n)).cumsum() % 55,
        'vol': 100000 + pd.Series(range(n)) * 1000
    })
    return df


def test_valid_dataframe_returns_figure():
    df = make_sample_df(30)
    fig = create_candlestick_chart(df, symbol="RB2605.SHF")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_empty_dataframe_returns_none():
    df = pd.DataFrame()
    fig = create_candlestick_chart(df)
    assert fig is None


def test_missing_required_columns_returns_none():
    df = pd.DataFrame({'trade_date': pd.date_range('2026-01-01', periods=10)})
    fig = create_candlestick_chart(df)
    assert fig is None


def test_column_name_mapping():
    df = make_sample_df(20)
    df = df.rename(columns={'trade_date': 'date', 'vol': 'volume'})
    fig = create_candlestick_chart(df, symbol="TEST")
    assert isinstance(fig, go.Figure)


def test_too_few_rows_returns_none():
    df = make_sample_df(1)
    fig = create_candlestick_chart(df)
    assert fig is None


def test_with_nan_values():
    df = make_sample_df(20)
    df.loc[5, 'close'] = None
    fig = create_candlestick_chart(df)
    assert isinstance(fig, go.Figure)


def test_main_contract_menu_integration():
    """Test new web menu feature with main contracts (AGENTS.md Test-First)"""
    from eaagent.tools.tushare_futures import get_popular_main_contracts, get_main_contracts
    popular = get_popular_main_contracts()
    assert len(popular) >= 5
    assert "RB2610.SHF" in popular

    main_list = get_main_contracts(limit=5)
    assert len(main_list) >= 1
    assert isinstance(main_list[0], dict)
    assert "ts_code" in main_list[0]

    # Test K-line with main contract
    df = pd.DataFrame({
        'trade_date': pd.date_range('2026-01-01', periods=30, freq='D'),
        'open': range(4000, 4030),
        'high': range(4010, 4040),
        'low': range(3990, 4020),
        'close': range(4005, 4035),
    })
    fig = create_candlestick_chart(df, symbol="RB2610.SHF")
    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "RB2610.SHF K线图" or "RB2610" in str(fig.layout.title)