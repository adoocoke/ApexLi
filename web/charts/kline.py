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
        return go.Figure()  # 返回空Figure避免 "figure_or_data" 错误

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
        return go.Figure()  # 返回空Figure避免 "figure_or_data" 错误

    # 4. 数据清洗
    df = df.dropna(subset=['open', 'high', 'low', 'close'])
    if len(df) < 2:
        print("[Kline] 有效K线数量不足（少于2根）")
        return go.Figure()  # 返回空Figure避免 "figure_or_data" 错误

    df = df.sort_values('trade_date').reset_index(drop=True)
    # 修复横轴: 强制trade_date为datetime (避免科学计数法) + index
    if 'trade_date' in df.columns:
        df['trade_date'] = pd.to_datetime(df['trade_date'], errors='coerce')
        print(f"[Kline] trade_date转换为datetime, 首条: {df['trade_date'].iloc[0] if not df.empty else 'N/A'}, 共{len(df)}条 (12个月数据)")
        # 确保datetime index (关键 for xaxis + signal date matching)
        if not isinstance(df.index, pd.DatetimeIndex):
            df = df.set_index('trade_date')
    else:
        print("[Kline] 无trade_date列，使用默认index")
        df.index = pd.date_range('2025-01-01', periods=len(df), freq='B')

    try:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.72, 0.28]
        )

        # ==================== K线 ====================
        x_data = df.index if isinstance(df.index, pd.DatetimeIndex) else df['trade_date']
        fig.add_trace(go.Candlestick(
            x=x_data,
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

        # **不显示MA13/任何均线** (用户最新要求: 生成图片/分析严格按Playbook量仓/背驰/定式, MA不在分析内容里)
        # 只保留纯K线 + 量柱 (K线tab仍可显示MA13如果计算, 但Vision图像无MA)
        if 'ma_13' in df.columns:
            print("[Kline] MA13已计算但根据Playbook要求不显示在Vision图像中 (仅用于Dashboard K线可选)")
        else:
            print("[Kline] 无MA13 (符合最新要求: 严格follow Playbook, 无均线)")

        # 成交量（按涨跌着色） - 兼容index
        x_for_vol = df.index if isinstance(df.index, pd.DatetimeIndex) else df.get('trade_date', range(len(df)))
        if 'vol' in df.columns or 'volume' in df.columns:
            vol_col = 'vol' if 'vol' in df.columns else 'volume'
            vol_colors = []
            for i in range(len(df)):
                close_val = df.iloc[i]['close']
                open_val = df.iloc[i]['open']
                if close_val >= open_val:
                    vol_colors.append('#FF0000')
                else:
                    vol_colors.append('#00CED1')
            fig.add_trace(go.Bar(
                x=x_for_vol,
                y=df[vol_col],
                name="成交量",
                marker_color=vol_colors
            ), row=2, col=1)
        else:
            print("[Kline] 无成交量列，跳过volume bar")

        # ==================== K线信号标注 (Phase 3 - EA LLM Signals) ====================
        if signals and len(signals) > 0:
            print(f"[Kline] 收到 {len(signals)} 个Signals, df行数 {len(df)} (12个月数据)")
            for i, sig in enumerate(signals):
                if i >= len(df): 
                    print(f"  Signal {i} 超出df范围, 跳过")
                    break
                # 关键修复: 使用reason中提取的日期 (Grok Vision Response **必须**包含具体日子如"2025-12-25")。**无日期的signal (index 5-8等) 必须被视为无效/观望**, 绝不标注
                reason = str(sig.get("reason", ""))
                import re
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', reason)
                if date_match:
                    target_date = pd.to_datetime(date_match.group(1))
                    # 找到df中最接近的日期行 (df现在有datetime index)
                    date_diffs = (df.index.to_series() - target_date).abs()
                    closest_idx = date_diffs.argmin()
                    row_idx = closest_idx
                    actual_date = df.index[row_idx].date() if hasattr(df.index[row_idx], 'date') else df.index[row_idx]
                    print(f"  Signal {i}: reason日期 {target_date.date()} → df行 {row_idx} (date={actual_date})")
                else:
                    # **无具体日期 = 无效signal (prompt已要求必须有日期 + 明确规则)**, 跳过标注, 视为观望
                    print(f"  Signal {i}: **无日期 (prompt已改进但LLM仍输出无日期signal)**, 跳过标注 (视为观望, 不应出现在Signals列表)")
                    continue  # 关键: 完全跳过无日期signal的标注

                direction = str(sig.get("direction", "")).lower()
                trend_sig = str(sig.get("trend_signal", sig.get("position_action", sig.get("direction", "")))).lower()
                conf = sig.get("confidence", 70)
                print(f"  Signal {i}: dir={direction[:10]}, trend={trend_sig[:15]}, conf={conf}, reason={reason[:60]}...")

                y_pos = float(df.iloc[row_idx]["close"])
                date = df.index[row_idx] if isinstance(df.index, pd.DatetimeIndex) else df.iloc[row_idx]["trade_date"]

                # 优先匹配卖平/买平 (修复: 买平/卖平标记缺失, 现在trend_sig/position_action优先于direction)
                if any(k in trend_sig + direction + reason for k in ["买平", "买入后平", "平仓", "减仓"]):
                    fig.add_annotation(
                        x=date, y=y_pos,
                        text="↗买平", showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor="#00AAFF", arrowwidth=2,
                        ax=0, ay=-40, font=dict(color="#00AAFF", size=11, family="Arial Black"), 
                        bgcolor="rgba(0,170,255,0.25)", bordercolor="#00AAFF"
                    )
                    print(f"  → 标注 ↗买平 at {date} (y={y_pos:.1f})")
                elif any(k in trend_sig + direction + reason for k in ["卖平", "平仓", "卖平(趋势结束)", "减仓", "震荡", "趋势结束", "趋势完结", "观望"]):
                    fig.add_annotation(
                        x=date, y=y_pos,
                        text="↘卖平", showarrow=True, arrowhead=1, arrowsize=1.2, arrowcolor="#FFAA00", arrowwidth=2,
                        ax=0, ay=40, font=dict(color="#FFAA00", size=10, family="Arial Black"), 
                        bgcolor="rgba(255,170,0,0.25)", bordercolor="#FFAA00"
                    )
                    print(f"  → 标注 ↘卖平 at {date} (y={y_pos:.1f})")
                elif any(k in direction + trend_sig + reason for k in ["买入", "多头", "buy", "long", "做多", "看多"]):
                    fig.add_annotation(
                        x=date, y=y_pos,
                        text="↑买入", showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor="#00FF00", arrowwidth=2,
                        ax=0, ay=-30, font=dict(color="#00FF00", size=11, family="Arial Black"), 
                        bgcolor="rgba(0,255,0,0.25)", bordercolor="#00FF00"
                    )
                    print(f"  → 标注 ↑买入 at {date} (y={y_pos:.1f})")
                elif any(k in direction + trend_sig + reason for k in ["卖出", "空头", "sell", "short", "做空", "看空", "趋势开启", "趋势开始"]):
                    fig.add_annotation(
                        x=date, y=y_pos,
                        text="↓卖出", showarrow=True, arrowhead=2, arrowsize=1.5, arrowcolor="#FF0000", arrowwidth=2,
                        ax=0, ay=30, font=dict(color="#FF0000", size=11, family="Arial Black"), 
                        bgcolor="rgba(255,0,0,0.25)", bordercolor="#FF0000"
                    )
                    print(f"  → 标注 ↓卖出 at {date} (y={y_pos:.1f})")
                else:
                    print(f"  → 无匹配关键词, direction={direction}, trend={trend_sig}, reason关键词={reason[:50]}")

        # ==================== 纯黑专业风格 ====================
        fig.update_layout(
            title=dict(text=f"{symbol} K线图 + Signals 标注 (12个月数据, {len(signals)} signals)", font=dict(color='white', size=15)),
            plot_bgcolor='#000000',
            paper_bgcolor='#000000',
            font=dict(color='#CCCCCC'),
            height=680,
            margin=dict(l=50, r=30, t=60, b=40),
            showlegend=True,
            legend=dict(font=dict(color='#AAAAAA', size=10), bgcolor='rgba(0,0,0,0.7)')
        )

        # 修复横轴: 强制日期格式 (避免20.252M科学计数法)
        fig.update_xaxes(
            type='date',
            tickformat='%Y-%m-%d',
            tickangle=45,
            gridcolor='#4A0000',
            linecolor='#660000',
            tickfont=dict(color='#AAAAAA', size=10)
        )
        fig.update_yaxes(gridcolor='#4A0000', linecolor='#660000', tickfont=dict(color='#AAAAAA', size=10))

        fig.update_yaxes(title_text="价格", row=1, col=1, title_font=dict(color='#AAAAAA'))
        fig.update_yaxes(title_text="成交量", row=2, col=1, title_font=dict(color='#AAAAAA'))
        fig.update_xaxes(rangeslider_visible=False)

        return fig

    except Exception as e:
        print(f"[Kline] 绘图异常: {e}")
        import traceback
        print(traceback.format_exc())
        return go.Figure()  # 返回空Figure避免 "figure_or_data" 错误