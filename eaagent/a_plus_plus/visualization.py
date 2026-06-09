import os
from datetime import datetime
from typing import Optional, Literal

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf

from .tools import get_futures_klines, detect_key_levels


def _find_recent_swing_lows(df: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    """找出最近的 swing low"""
    lows = df['low'].values
    swing_lows = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_lows.append((df.index[i], lows[i]))
    return pd.DataFrame(swing_lows[-n:], columns=['date', 'price']) if swing_lows else pd.DataFrame()


def _find_recent_swing_highs(df: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    """找出最近的 swing high"""
    highs = df['high'].values
    swing_highs = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_highs.append((df.index[i], highs[i]))
    return pd.DataFrame(swing_highs[-n:], columns=['date', 'price']) if swing_highs else pd.DataFrame()


def _calculate_parallel_channel(df: pd.DataFrame, trend: str) -> Optional[dict]:
    """计算平行趋势通道"""
    if trend == "up":
        points = _find_recent_swing_lows(df, n=2)
        if len(points) < 2:
            return None
        # 下轨：两个低点连线
        x1, y1 = 0, points.iloc[0]['price']
        x2, y2 = len(df) - 1, points.iloc[1]['price']
        slope = (y2 - y1) / (x2 - x1) if x2 != x1 else 0

        # 上轨：找一个 swing high 确定宽度
        highs = _find_recent_swing_highs(df, n=1)
        if len(highs) == 0:
            width = (df['high'].max() - df['low'].min()) * 0.6
        else:
            width = highs.iloc[0]['price'] - y2

        upper_line = [y1 + width + slope * i for i in range(len(df))]
        lower_line = [y1 + slope * i for i in range(len(df))]

        return {
            "upper": upper_line,
            "lower": lower_line,
            "type": "up"
        }

    elif trend == "down":
        points = _find_recent_swing_highs(df, n=2)
        if len(points) < 2:
            return None
        x1, y1 = 0, points.iloc[0]['price']
        x2, y2 = len(df) - 1, points.iloc[1]['price']
        slope = (y2 - y1) / (x2 - x1) if x2 != x1 else 0

        lows = _find_recent_swing_lows(df, n=1)
        if len(lows) == 0:
            width = (df['high'].max() - df['low'].min()) * 0.6
        else:
            width = y2 - lows.iloc[0]['price']

        upper_line = [y1 + slope * i for i in range(len(df))]
        lower_line = [y1 - width + slope * i for i in range(len(df))]

        return {
            "upper": upper_line,
            "lower": lower_line,
            "type": "down"
        }

    return None


def plot_kline_with_channel(
    symbol: str,
    period: Literal["D", "30"] = "D",
    trend: Optional[Literal["up", "down"]] = None,
    lookback: int = 60,
    show_ma20: bool = True,
    show_key_levels: bool = True,
    save_dir: str = "artifacts/charts"
) -> str:
    """
    绘制K线图 + MA20 + 支撑压力位 + 趋势通道
    trend: "up" 表示上升通道, "down" 表示下降通道
    """
    os.makedirs(save_dir, exist_ok=True)

    df = get_futures_klines(symbol, period=period, limit=lookback)
    if df.empty:
        raise ValueError(f"无法获取 {symbol} 的 {period} 数据")

    df = df.set_index("trade_date")
    df.index = pd.to_datetime(df.index)

    # 计算 MA20
    df['ma20'] = df['close'].rolling(window=20).mean()

    # 获取关键位
    key_levels = detect_key_levels(df.reset_index(), lookback=lookback)

    # 准备添加的线
    addplots = []
    if show_ma20:
        addplots.append(mpf.make_addplot(df['ma20'], color='orange', width=1.2))

    # 趋势通道
    channel = None
    if trend in ["up", "down"]:
        channel = _calculate_parallel_channel(df.reset_index(), trend)
        if channel:
            addplots.append(mpf.make_addplot(channel["upper"], color='blue', linestyle='--', width=1.0))
            addplots.append(mpf.make_addplot(channel["lower"], color='blue', linestyle='--', width=1.0))

    # 支撑压力位（水平线）
    if show_key_levels and key_levels["resistances"]:
        for level in key_levels["resistances"]:
            addplots.append(mpf.make_addplot([level] * len(df), color='red', linestyle=':', width=0.8))
    if show_key_levels and key_levels["supports"]:
        for level in key_levels["supports"]:
            addplots.append(mpf.make_addplot([level] * len(df), color='green', linestyle=':', width=0.8))

    # 保存路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{period}_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)

    # 绘图
    mpf.plot(
        df,
        type='candle',
        style='charles',
        title=f"{symbol} {period} K线图",
        ylabel='Price',
        addplot=addplots if addplots else None,
        figsize=(12, 6),
        savefig=filepath
    )

    print(f"✅ K线图已保存至: {filepath}")
    return filepath
