import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import tushare as ts


def get_futures_daily_recent(
    ts_code: str,
    months: int = 3,
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    获取指定期货合约最近 N 个月的日线数据

    Args:
        ts_code: 期货合约代码，例如 'RB2609.SHF'
        months: 获取最近几个月的数据，默认 3 个月
        pro: tushare pro_api 对象，如果为 None 则自动初始化

    Returns:
        pandas DataFrame，包含日线数据
    """
    if pro is None:
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("环境变量 TUSHARE_TOKEN 未设置")
        ts.set_token(token)
        pro = ts.pro_api()

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)

    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    df = pro.fut_daily(
        ts_code=ts_code,
        start_date=start_date_str,
        end_date=end_date_str
    )

    if df is None or df.empty:
        return pd.DataFrame()

    # 按交易日期排序
    df = df.sort_values("trade_date").reset_index(drop=True)
    return df
