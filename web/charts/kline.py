import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional

def create_candlestick_chart(df: pd.DataFrame, symbol: str = "", signals: list = None) -> Optional[go.Figure]:
    """
    专业期货K线图 + EA LLM Signals 标注 (Phase 3)
    - 上涨：空心红色 / 下跌：实心青色
    - 纯黑专业风格
    - 新增: Signals 箭头标注 (买入绿↑ / 卖出红↓ / 卖平橙)
    """
    # 1. 输入校验
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        print("[Kline] 输入数据为空或类型错误")
        return None

    df = df.copy()
    signals = signals or []

    # 2. 列名标准化（兼容多种常见命名）
    column_mapping = {
        'date': 'trade_date',
        'datetime': 'trade_date',
        'time': 'trade_date',
        'volume': 'vol',
        'amount': 'amount',
    }
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df[new_col] = df[old_col]

    # 3. 检查必要列
    required_cols = ['trade_date', 'open', 'high', 'low', 'close']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[Kline] 缺少必要列: {missing}")
        return None

    # 4. 数据清洗
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    if len(df) < 2:
        print("[Kline] 有效K线数量不足（少于2根）")
        return None

    df = df.sort_values('trade_date').reset_index(drop=True)

    try:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.72, 0.28]
        )

        # ==================== K线 ====================
        fig.add_trace(go.Candlestick(
            x=df['trade_date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="K线",
            increasing_line_color='#FF0000',           # 红框
            increasing_fillcolor='rgba(0,0,0,0)',      # 空心
            increasing_line_width=1.3,
            decreasing_line_color='#00CED1',           # 青色
            decreasing_fillcolor='#00CED1',            # 实心浅蓝
            decreasing_line_width=1.0,
        ), row=1, col=1)

        # 均线
        ma_style = {
            'ma_5':  {'color': '#FFD700', 'width': 1.4},
            'ma_13': {'color': '#00FF7F', 'width': 1.4},
            'ma_20': {'color': '#FF69B4', 'width': 1.4},
        }
        for ma_col, style in ma_style.items():
            if ma_col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['trade_date'],
                    y=df[ma_col],
                    name=ma_col.upper(),
                    line=dict(color=style['color'], width=style['width'])
                ), row=1, col=1)

        # 成交量（按涨跌着色）
        if 'vol' in df.columns:
            vol_colors = []
            for i in range(len(df)):
                if df.loc[i, 'close'] >= df.loc[i, 'open']:
                    vol_colors.append('#FF0000')      # 红量
                else:
                    vol_colors.append('#00CED1')      # 青量
            fig.add_trace(go.Bar(
                x=df['trade_date'],
                y=df['vol'],
                name="成交量",
                marker_color=vol_colors
            ), row=2, col=1)

        # ==================== K线信号标注 (Phase 3 - EA LLM Signals) ====================
        if signals and len(signals) > 0:
            for i, sig in enumerate(signals):
                if i >= len(df): break
                row_idx = i  # align with df rows
                direction = str(sig.get("direction", "")).lower()
                trend_sig = str(sig.get("trend_signal", sig.get("position_action", ""))).lower()
                conf = sig.get("confidence", 70)
                if conf < 70: continue  # 只标注高置信 signal

                # 信号位置 (close price)
                y_pos = float(df.iloc[row_idx]["close"])
                date = df.iloc[row_idx]["trade_date"]

                if any(k in direction + trend_sig for k in ["买入", "多头", "buy", "long", "做多"]):
                    fig.add_annotation(
                        x=date, y=y_pos * 0.995,
                        text="↑ 买入", showarrow=True, arrowhead=2, arrowcolor="#00FF00",
                        font=dict(color="#00FF00", size=12), bgcolor="rgba(0,255,0,0.2)"
                    )
                elif any(k in direction + trend_sig for k in ["卖出", "空头", "sell", "short", "做空", "趋势开启"]):
                    fig.add_annotation(
                        x=date, y=y_pos * 1.005,
                        text="↓ 卖出", showarrow=True, arrowhead=2, arrowcolor="#FF0000",
                        font=dict(color="#FF0000", size=12), bgcolor="rgba(255,0,0,0.2)"
                    )
                elif any(k in direction + trend_sig for k in ["卖平", "平仓", "卖平(趋势结束)", "减仓", "震荡"]):
                    fig.add_annotation(
                        x=date, y=y_pos * 1.01,
                        text="↘ 卖平", showarrow=True, arrowhead=1, arrowcolor="#FFAA00",
                        font=dict(color="#FFAA00", size=11), bgcolor="rgba(255,170,0,0.2)"
                    )

        # ==================== 纯黑专业风格 ====================
        fig.update_layout(
            title=dict(text=f"{symbol} K线图 + Signals 标注", font=dict(color='white', size=15)),
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#CCCCCC'),
            height=680,
            margin=dict(l=50, r=30, t=50, b=40),
            showlegend=True,
            legend=dict(font=dict(color='#AAAAAA', size=10), bgcolor='rgba(0,0,0,0.7)')
        )

        fig.update_xaxes(gridcolor='#4A0000', linecolor='#660000', tickfont=dict(color='#AAAAAA', size=10))
        fig.update_yaxes(gridcolor='#4A0000', linecolor='#660000', tickfont=dict(color='#AAAAAA', size=10))

        fig.update_yaxes(title_text="价格", row=1, col=1, title_font=dict(color='#AAAAAA'))
        fig.update_yaxes(title_text="成交量", row=2, col=1, title_font=dict(color='#AAAAAA'))
        fig.update_xaxes(rangeslider_visible=False)

        return fig

    except Exception as e:
        print(f"[Kline] 绘图异常: {e}")
        return None