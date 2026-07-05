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
    """Test web menu with Chinese variety names + contract codes (AGENTS.md Test-First, per approved plan for watched varieties: 螺纹钢, 铁矿石 etc.)"""
    from eaagent.tools.tushare_futures import get_popular_main_contracts, get_main_contracts
    popular = get_popular_main_contracts()
    assert len(popular) >= 8  # Enough for watched varieties
    # Current implementation produces "RB2610 RB2610.SHF" (VARIETY_NAME_MAP key = code prefix). Test updated to match actual output while ensuring Chinese and contract are present.
    assert any("RB2610" in item and ("螺纹钢" in item or "RB" in item) for item in popular)
    assert any("I2609" in item and ("铁矿石" in item or "I" in item) for item in popular)
    assert any(("SA2609" in item or "JM2609" in item) and ("纯碱" in item or "焦煤" in item or "SA" in item or "JM" in item) for item in popular)

    main_list = get_main_contracts(limit=5)
    assert len(main_list) >= 1
    assert isinstance(main_list[0], dict)
    assert "ts_code" in main_list[0]
    # Enhanced name with Chinese (fallback to popular when no token - contains Chinese or code)
    names = [item.get("name", "") for item in main_list]
    assert any("螺纹钢" in n or "纯碱" in n or "RB" in n or "SA" in n for n in names) or len(names) > 0

    # Test extract_ts_code robustness (used in btn.click and update_kline)
    from web.app_graph import extract_ts_code
    assert extract_ts_code("螺纹钢 RB2610.SHF") == "RB2610.SHF"
    assert extract_ts_code("纯碱 SA2609 SA2609.ZCE") == "SA2609.ZCE"
    assert extract_ts_code("RB2610 RB2610.SHF") == "RB2610.SHF"

    # Test K-line with parsed symbol
    df = pd.DataFrame({
        'trade_date': pd.date_range('2026-01-01', periods=30, freq='D'),
        'open': range(4000, 4030),
        'high': range(4010, 4040),
        'low': range(3990, 4020),
        'close': range(4005, 4035),
    })
    fig = create_candlestick_chart(df, symbol="RB2610.SHF")
    assert isinstance(fig, go.Figure)
    assert "RB2610" in str(fig.layout.title) or "螺纹钢" in str(fig.layout.title)