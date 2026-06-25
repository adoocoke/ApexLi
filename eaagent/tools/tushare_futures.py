import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Union
import tushare as ts

def get_futures_daily_recent(
    ts_code: str,
    months: int = 5,
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    获取期货最近 N 个月的日线数据（包含 oi_chg）
    默认使用最近 5 个月数据
    """
    if pro is None:
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("请设置环境变量 TUSHARE_TOKEN")
        pro = ts.pro_api(token)

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=months * 30 + 10)).strftime("%Y%m%d")

    try:
        df = pro.fut_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields="ts_code,trade_date,open,high,low,close,settle,vol,amount,oi,oi_chg"
        )
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.sort_values("trade_date").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[Tushare] 获取 {ts_code} 日线失败: {e}")
        return pd.DataFrame()


def get_related_futures_daily(
    symbols: List[str],
    months: int = 5,
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    获取多个相关期货品种的日线数据（复用 get_futures_daily_recent）
    例如：铁矿石、焦炭、焦煤等
    """
    all_data = []
    for symbol in symbols:
        df = get_futures_daily_recent(symbol, months=months, pro=pro)
        if not df.empty:
            all_data.append(df)

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


def get_futures_daily_with_ma(
    ts_code: str,
    months: int = 5,
    ma_periods: List[int] = [5, 13, 20],
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    使用 pro_bar 接口获取期货日线 + 均线数据
    注意：获取均线时需要往前多取日期
    """
    if pro is None:
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("请设置环境变量 TUSHARE_TOKEN")
        pro = ts.pro_api(token)

    # 计算需要往前多取的天数（取最大均线周期的 1.5 倍）
    max_ma = max(ma_periods) if ma_periods else 20
    extra_days = int(max_ma * 1.5) + 10

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=months * 30 + extra_days)).strftime("%Y%m%d")

    try:
        df = pro.pro_bar(
            ts_code=ts_code,
            asset='FT',                    # 期货
            start_date=start_date,
            end_date=end_date,
            freq='D',
            ma=ma_periods
        )

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.sort_values("trade_date").reset_index(drop=True)
        return df

    except Exception as e:
        print(f"[Tushare] pro_bar 获取 {ts_code} 带均线数据失败: {e}")
        return pd.DataFrame()
