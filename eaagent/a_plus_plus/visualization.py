import os
from datetime import datetime
from typing import Literal

import pandas as pd
import mplfinance as mpf

from .tools import get_futures_klines, detect_key_levels


def plot_kline_with_levels(
    symbol: str,
    period: Literal["D", "30"] = "D",
    lookback: int = 60,
    show_ma20: bool = True,
    save_dir: str = "artifacts/charts"
) -> str:
    """
    K线图（深灰背景 + 红色上涨 + 浅蓝色下跌）
    + MA20 + 射线式支撑压力位
    """
    os.makedirs(save_dir, exist_ok=True)

    df = get_futures_klines(symbol, period=period, limit=lookback)
    if df.empty:
        raise ValueError(f"无法获取 {symbol} 的 {period} 数据")

    df = df.set_index("trade_date")
    df.index = pd.to_datetime(df.index)
    df['ma20'] = df['close'].rolling(window=20).mean()

    key_levels = detect_key_levels(df.reset_index(), lookback=lookback)

    # 自定义市场颜色
    mc = mpf.make_marketcolors(
        up='red',                    # 上涨K线：红色
        down='#81D4FA',              # 下跌K线：浅蓝色
        edge='inherit',
        wick='inherit',
        volume='inherit'
    )

    # 自定义深灰背景样式
    s = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors=mc,
        figcolor='#2C2C2C',          # 整体背景（深灰）
        facecolor='#2C2C2C',         # 绘图区域背景（深灰）
        edgecolor='#AAAAAA',
        gridcolor='#555555',
        gridstyle='--',
        y_on_right=False
    )

    addplots = []
    if show_ma20:
        addplots.append(mpf.make_addplot(df['ma20'], color='#FFEB3B', width=1.3))  # 黄色MA20

    # 压力位（绿色虚线）
    for item in key_levels.get("resistances", []):
        level = item["price"]
        idx = item.get("index", 0)
        arr = [float('nan')] * len(df)
        arr[idx:] = [level] * (len(df) - idx)
        addplots.append(mpf.make_addplot(arr, color='#4CAF50', linestyle='--', width=0.9))

    # 支撑位（红色虚线）
    for item in key_levels.get("supports", []):
        level = item["price"]
        idx = item.get("index", 0)
        arr = [float('nan')] * len(df)
        arr[idx:] = [level] * (len(df) - idx)
        addplots.append(mpf.make_addplot(arr, color='#E53935', linestyle='--', width=0.9))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{period}_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)

    mpf.plot(
        df,
        type='candle',
        style=s,
        title=f"{symbol} {period} K线 + 关键位",
        ylabel='Price',
        addplot=addplots if addplots else None,
        figsize=(13, 7),
        savefig=filepath
    )

    print(f"✅ K线图已保存至: {filepath}")
    return filepath
