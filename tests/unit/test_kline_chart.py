import pandas as pd
import pytest
from web.charts.kline import create_candlestick_chart
import plotly.graph_objects as go

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
    assert isinstance(fig, go.Figure)   # 应该自动清理NaN后绘图