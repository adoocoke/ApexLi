import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional


def create_candlestick_chart(df: pd.DataFrame, symbol: str) -> Optional[go.Figure]:
    """
    生成 Plotly 交互式 K线图（包含均线 + 成交量）
    """
    if df is None or df.empty:
        return None

    # 确保按日期排序
    if 'trade_date' in df.columns:
        df = df.sort_values('trade_date').reset_index(drop=True)

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3]
    )

    # K线
    fig.add_trace(go.Candlestick(
        x=df['trade_date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="K线"
    ), row=1, col=1)

    # 均线
    for ma_col, ma_name in [('ma_5', 'MA5'), ('ma_13', 'MA13'), ('ma_20', 'MA20')]:
        if ma_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['trade_date'],
                y=df[ma_col],
                name=ma_name,
                line=dict(width=1.5)
            ), row=1, col=1)

    # 成交量
    if 'vol' in df.columns:
        fig.add_trace(go.Bar(
            x=df['trade_date'],
            y=df['vol'],
            name="成交量",
            marker_color='rgba(100,100,100,0.5)'
        ), row=2, col=1)

    fig.update_layout(
        title=f"{symbol} K线图 + 均线",
        xaxis_rangeslider_visible=False,
        height=650,
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)

    return fig
