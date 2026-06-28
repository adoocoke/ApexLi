import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def create_candlestick_chart(df: pd.DataFrame, symbol: str) -> Optional[go.Figure]:
    """
    健壮版 K线图绘制（深色专业风格）
    - 上涨 K线 = 红色
    - 下跌 K线 = 蓝色
    - 深色背景主题
    """
    if df is None or df.empty:
        print("[Kline] DataFrame 为空，无法绘图")
        return None

    # 兼容不同列名
    df = df.copy()
    if 'trade_date' not in df.columns and 'date' in df.columns:
        df['trade_date'] = df['date']
    if 'vol' not in df.columns and 'volume' in df.columns:
        df['vol'] = df['volume']

    required_cols = ['trade_date', 'open', 'high', 'low', 'close']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[Kline] 缺少必要列: {missing}")
        return None

    try:
        df = df.sort_values('trade_date').reset_index(drop=True)

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3]
        )

        # ==================== K线（核心修改） ====================
        fig.add_trace(go.Candlestick(
            x=df['trade_date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="K线",
            # 上涨 = 红色
            increasing_line_color='red',
            increasing_fillcolor='rgba(255, 50, 50, 0.85)',
            # 下跌 = 蓝色
            decreasing_line_color='blue',
            decreasing_fillcolor='rgba(50, 120, 255, 0.85)',
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

        # 成交量（适配深色背景）
        if 'vol' in df.columns:
            fig.add_trace(go.Bar(
                x=df['trade_date'],
                y=df['vol'],
                name="成交量",
                marker_color='rgba(180, 180, 180, 0.65)'
            ), row=2, col=1)

        # ==================== 深色主题 ====================
        fig.update_layout(
            title=dict(
                text=f"{symbol} K线图 + 均线",
                font=dict(color='#e0e0e0', size=16)
            ),
            xaxis_rangeslider_visible=False,
            height=650,
            showlegend=True,
            margin=dict(l=40, r=40, t=60, b=40),
            # 深色背景
            plot_bgcolor='#1a1a2e',
            paper_bgcolor='#0f0f1a',
            font=dict(color='#d0d0d0'),
            legend=dict(
                font=dict(color='#d0d0d0'),
                bgcolor='rgba(30, 30, 46, 0.85)'
            )
        )

        # 坐标轴样式（适配深色背景）
        fig.update_xaxes(
            gridcolor='#2a2a4a',
            linecolor='#3a3a5a',
            tickfont=dict(color='#b0b0b0')
        )
        fig.update_yaxes(
            gridcolor='#2a2a4a',
            linecolor='#3a3a5a',
            tickfont=dict(color='#b0b0b0'),
            title_font=dict(color='#b0b0b0')
        )

        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)

        return fig

    except Exception as e:
        print(f"[Kline] 绘图出错: {e}")
        return None