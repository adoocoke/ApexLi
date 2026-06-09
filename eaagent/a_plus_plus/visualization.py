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
    绘制K线图 + MA20 + 射线式支撑压力位
    - 支撑位：红色虚线（从实际位置向右延长）
    - 压力位：绿色虚线（从实际位置向右延长）
    """
    os.makedirs(save_dir, exist_ok=True)

    df = get_futures_klines(symbol, period=period, limit=lookback)
    if df.empty:
        raise ValueError(f"无法获取 {symbol} 的 {period} 数据")

    df = df.set_index("trade_date")
    df.index = pd.to_datetime(df.index)
    df['ma20'] = df['close'].rolling(window=20).mean()

    key_levels = detect_key_levels(df.reset_index(), lookback=lookback)

    addplots = []
    if show_ma20:
        addplots.append(mpf.make_addplot(df['ma20'], color='#FFEB3B', width=1.3))

    # 压力位（绿色，从对应位置向右延长）
    for item in key_levels.get("resistances", []):
        level = item["price"]
        idx = item.get("index", 0)
        arr = [float('nan')] * len(df)
        arr[idx:] = [level] * (len(df) - idx)
        addplots.append(mpf.make_addplot(arr, color='#4CAF50', linestyle='--', width=0.9))

    # 支撑位（红色，从对应位置向右延长）
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
        style='nightclouds',
        title=f"{symbol} {period} K线 + 关键位",
        ylabel='Price',
        addplot=addplots if addplots else None,
        figsize=(13, 7),
        savefig=filepath
    )

    print(f"✅ K线图已保存至: {filepath}")
    return filepath


def generate_kline_chart(symbol: str, period: str = "D") -> str:
    """
    【Agent 可调用工具】
    生成K线图（包含支撑压力位），并返回图片路径。
    Agent 可以在分析关键位时主动调用此工具。
    """
    try:
        path = plot_kline_with_levels(symbol, period=period)
        return f"已成功生成K线图，保存路径为：{path}。你可以查看图中的支撑位和压力位辅助分析。"
    except Exception as e:
        return f"生成K线图失败，错误信息：{str(e)}"
