"""
Tushare 期货数据工具（A计划 - 20260605）
优化返回格式，使其更适合 ReAct Agent 进行推理
"""

import os
from typing import Optional
from datetime import datetime
import pandas as pd

try:
    import tushare as ts
except ImportError:
    ts = None


def _get_pro_api():
    if ts is None:
        raise ImportError("请先安装 tushare: pip install tushare")

    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError("未找到 TUSHARE_TOKEN 环境变量，请先设置")

    ts.set_token(token)
    return ts.pro_api()


def _format_futures_summary(df: pd.DataFrame, ts_code: str) -> str:
    """将 DataFrame 格式化为适合 Agent 使用的简洁摘要"""
    if df.empty:
        return f"未查询到 {ts_code} 的数据"

    df = df.sort_values("trade_date")
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else None

    # 计算涨跌
    if prev is not None:
        change = latest["close"] - prev["close"]
        change_str = f"{change:+.2f}"
    else:
        change_str = "--"

    # 基础统计
    high = df["high"].max()
    low = df["low"].min()
    avg_vol = df["vol"].mean()

    # 最近数据（最多显示 6 条）
    recent = df.tail(6)

    lines = [
        f"【{ts_code}】查询区间: {df['trade_date'].iloc[0]} ~ {df['trade_date'].iloc[-1]}",
        f"最新收盘: {latest['close']:.2f} ({change_str})",
        f"区间最高: {high:.2f} / 最低: {low:.2f}",
        f"平均成交量: {int(avg_vol):,} 手",
        "",
        "最近交易日数据："
    ]

    for _, row in recent.iterrows():
        lines.append(
            f"{row['trade_date']} | "
            f"收:{row['close']:.2f} | "
            f"涨跌:{row['close'] - prev['close'] if prev is not None else '--':+.2f} | "
            f"持仓:{int(row['oi']):,}"
        )
        prev = row  # 更新 prev 用于下一行计算

    return "\n".join(lines)


def get_futures_daily(
    ts_code: str,
    start_date: str,
    end_date: Optional[str] = None,
) -> str:
    """
    获取期货日线数据并返回结构化摘要（优化版）

    Returns:
        适合 Agent 推理的简洁格式字符串
    """
    pro = _get_pro_api()

    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    try:
        df = pro.fut_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields="ts_code,trade_date,open,high,low,close,vol,amount,oi"
        )

        if df.empty:
            return f"未查询到 {ts_code} 在 {start_date} 到 {end_date} 的数据"

        return _format_futures_summary(df, ts_code)

    except Exception as e:
        return f"Tushare 查询失败: {str(e)}"
