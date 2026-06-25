import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import tushare as ts
import re

def _get_correct_exchange(symbol: str) -> str:
    """根据品种前缀自动判断交易所"""
    prefix = re.match(r'([A-Z]+)', symbol.upper())
    if not prefix:
        return 'SHF'
    
    p = prefix.group(1)
    
    # 大连商品交易所 (DCE)
    dce_prefixes = ['I', 'JM', 'J', 'A', 'M', 'Y', 'P', 'C', 'CS', 'PP', 'L', 'V', 'EG', 'RR', 'BB', 'FB']
    if p in dce_prefixes:
        return 'DCE'
    
    # 上海期货交易所 (SHF)
    shf_prefixes = ['RB', 'HC', 'CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'BU', 'RU', 'FU', 'SC', 'NR']
    if p in shf_prefixes:
        return 'SHF'
    
    # 郑州商品交易所 (CZCE)
    czce_prefixes = ['SR', 'CF', 'TA', 'MA', 'FG', 'ZC', 'OI', 'RM', 'RS', 'SF', 'SM', 'UR', 'SA', 'PF', 'AP', 'CJ', 'PK']
    if p in czce_prefixes:
        return 'CZCE'
    
    return 'SHF'  # 默认


def get_futures_daily_recent(
    ts_code: str,
    months: int = 5,
    pro: Optional[object] = None
) -> pd.DataFrame:
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
    months: int = 3,
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    获取多个相关期货品种的日线数据。
    自动根据品种前缀修正交易所后缀（I/JM/J → DCE）
    """
    all_data = []

    for raw_symbol in symbols:
        # 自动修正交易所
        if '.' not in raw_symbol:
            exchange = _get_correct_exchange(raw_symbol)
            symbol = f"{raw_symbol}.{exchange}"
        else:
            symbol = raw_symbol

        df = get_futures_daily_recent(symbol, months=months, pro=pro)

        if df.empty:
            print(f"[Data] {symbol} 无数据，尝试自动修正交易所...")
            # 如果还是拿不到，尝试其他交易所
            for ex in ['DCE', 'SHF', 'CZCE']:
                test_symbol = f"{raw_symbol.split('.')[0]}.{ex}"
                df = get_futures_daily_recent(test_symbol, months=months, pro=pro)
                if not df.empty:
                    print(f"[Data] 成功切换到 {test_symbol}")
                    break

        if not df.empty:
            all_data.append(df)
        else:
            print(f"[Data] {raw_symbol} 所有交易所均无数据")

    if not all_data:
        return pd.DataFrame()

    return pd.concat(all_data, ignore_index=True)


def get_futures_daily_with_ma(
    ts_code: str,
    months: int = 5,
    ma_periods: List[int] = [5, 13, 20],
    pro: Optional[object] = None
) -> pd.DataFrame:
    if pro is None:
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("请设置环境变量 TUSHARE_TOKEN")
        pro = ts.pro_api(token)

    max_ma = max(ma_periods) if ma_periods else 20
    extra_days = int(max_ma * 1.5) + 10

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=months * 30 + extra_days)).strftime("%Y%m%d")

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

        for period in ma_periods:
            df[f"ma_{period}"] = df["close"].rolling(window=period).mean()

        target_start = (datetime.now() - timedelta(days=months * 30)).strftime("%Y%m%d")
        df = df[df["trade_date"] >= target_start].reset_index(drop=True)

        return df
    except Exception as e:
        print(f"[Tushare] 获取 {ts_code} 带均线数据失败: {e}")
        return pd.DataFrame()
