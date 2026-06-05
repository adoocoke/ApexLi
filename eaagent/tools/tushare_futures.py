"""
Tushare 期货数据工具
需要先安装: pip install tushare
并设置环境变量 TUSHARE_TOKEN
"""

import os
from typing import Optional
import pandas as pd

try:
    import tushare as ts
except ImportError:
    ts = None


def _get_pro_api():
    """获取 Tushare Pro API 实例"""
    if ts is None:
        raise ImportError("请先安装 tushare: pip install tushare")

    token = os.getenv("TUSHARE_TOKEN")
    if not token:
        raise ValueError(
            "未找到 TUSHARE_TOKEN 环境变量。\n"
            "请先去 https://tushare.pro 注册并获取 token，"
            "然后设置环境变量：export TUSHARE_TOKEN=你的token"
        )

    ts.set_token(token)
    return ts.pro_api()


def get_futures_daily(
    ts_code: str,
    start_date: str,
    end_date: Optional[str] = None,
) -> str:
    """
    获取期货日线数据（使用 Tushare Pro）

    Args:
        ts_code: 期货代码，例如 "RB2405.SHF" 或 "I2409.DCE"
        start_date: 开始日期，格式 YYYYMMDD，例如 "20240101"
        end_date: 结束日期，格式 YYYYMMDD，默认为今天

    Returns:
        格式化的日线数据字符串
    """
    pro = _get_pro_api()

    if end_date is None:
        from datetime import datetime
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

        # 按日期排序
        df = df.sort_values("trade_date")

        # 取最近 10 条展示
        recent = df.tail(10)

        result = f"【{ts_code} 日线数据】最近 {len(recent)} 条记录：\n"
        for _, row in recent.iterrows():
            result += (
                f"{row['trade_date']} | "
                f"开:{row['open']:.2f} 高:{row['high']:.2f} "
                f"低:{row['low']:.2f} 收:{row['close']:.2f} "
                f"持仓:{int(row['oi'])} 成交:{int(row['vol'])}\n"
            )

        return result.strip()

    except Exception as e:
        return f"查询 Tushare 数据失败: {str(e)}"


# 便捷函数：支持简单品种代码（如 RB、I、MA）
def get_futures_daily_simple(
    symbol: str,
    start_date: str,
    end_date: Optional[str] = None,
    exchange: str = "SHF"
) -> str:
    """
    简化版获取期货日线（自动补全 ts_code）

    Args:
        symbol: 品种代码，如 "RB", "I", "MA", "CU"
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
        exchange: 交易所代码，默认 SHF（上期所），可选 DCE, CZCE, INE
    """
    # 简单映射常见主力合约（实际使用建议传入具体合约如 RB2405.SHF）
    ts_code = f"{symbol}2405.{exchange}"  # 这里简化处理，实际应动态获取主力合约
    return get_futures_daily(ts_code, start_date, end_date)