"""
Tushare 期货分钟线数据工具
"""

import os
from typing import Optional
from datetime import datetime, timedelta
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
        raise ValueError("未找到 TUSHARE_TOKEN 环境变量")

    ts.set_token(token)
    return ts.pro_api()


def get_futures_minute(
    ts_code: str,
    start_date: str,
    end_date: Optional[str] = None,
    freq: str = "1min"
) -> str:
    """
    获取期货分钟线数据

    Args:
        ts_code: 合约代码，例如 "RB2405.SHF"
        start_date: 开始时间，格式 YYYYMMDD 或 YYYYMMDDHHMMSS
        end_date: 结束时间
        freq: 频率，支持 1min, 5min, 15min, 30min, 60min

    Returns:
        格式化后的分钟线摘要字符串
    """
    pro = _get_pro_api()

    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d%H%M%S")

    try:
        df = pro.fut_min(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            freq=freq
        )

        if df.empty:
            return f"未查询到 {ts_code} 的 {freq} 数据"

        df = df.sort_values("trade_time")

        # 取最近 10 条
        recent = df.tail(10)

        result = f"【{ts_code} {freq} 数据】最近 {len(recent)} 条\n"
        for _, row in recent.iterrows():
            result += (
                f"{row['trade_time']} | "
                f"O:{row['open']:.2f} H:{row['high']:.2f} "
                f"L:{row['low']:.2f} C:{row['close']:.2f} "
                f"Vol:{int(row['vol'])}\n"
            )

        return result.strip()

    except Exception as e:
        return f"查询分钟线失败: {str(e)}"
