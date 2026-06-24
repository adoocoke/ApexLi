import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import tushare as ts

def get_futures_daily_recent(
    ts_code: str, 
    months: int = 5,           # ← 默认改为 5 个月
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    获取期货最近 N 个月的日线数据（包含 oi_chg）
    默认使用最近 5 个月数据，适合主力合约分析
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
