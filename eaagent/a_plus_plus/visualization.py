import os
from datetime import datetime
from typing import Optional, Literal

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
    绘制K线图 + MA20 + 支撑位 + 压力位
    - 支撑位：红色虚线
    - 压力位：绿色虚线
    """
    os.makedirs(save_dir, exist_ok=True)

    df = get_futures_klines(symbol, period=period, limit=lookback)
    if df.empty:
        raise ValueError(f"无法获取 {symbol} 的 {period} 数据")

    df = df.set_index("trade_date")
    df.index = pd.to_datetime(df.index)
    df['ma20'] = df['close'].rolling(window=20).mean()

    # 获取关键位
    key_levels = detect_key_levels(df.reset_index(), lookback=lookback)

    addplots = []
    if show_ma20:
        addplots.append(mpf.make_addplot(df['ma20'], color='orange', width=1.5))

    # 压力位（绿色虚线）
    for level in key_levels.get("resistances", []):
        addplots.append(mpf.make_addplot([level] * len(df), color='green', linestyle='--', width=1.2))

    # 支撑位（红色虚线）
    for level in key_levels.get("supports", []):
        addplots.append(mpf.make_addplot([level] * len(df), color='red', linestyle='--', width=1.2))

    # 保存路径
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{symbol}_{period}_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)

    mpf.plot(
        df,
        type='candle',
        style='charles',
        title=f"{symbol} {period} K线 + 关键位",
        ylabel='Price',
        addplot=addplots if addplots else None,
        figsize=(12, 6),
        savefig=filepath
    )

    print(f"✅ K线图已保存至: {filepath}")
    return filepath
