import pandas as pd
import tushare as ts
from typing import Any, Dict, Optional
from datetime import datetime

from .base import DataProvider


class TushareStockProvider(DataProvider):
    """Tushare A股数据提供者实现"""

    def __init__(self, token: str | None = None, pro: Any = None):
        if pro is not None:
            self.pro = pro
        else:
            if token:
                ts.set_token(token)
            self.pro = ts.pro_api()

    def _normalize_symbol(self, symbol: str) -> str:
        if "." in symbol:
            return symbol.upper()
        # 简单自动补全：6开头 -> .SH，其余 -> .SZ
        if symbol.startswith("6"):
            return f"{symbol}.SH"
        else:
            return f"{symbol}.SZ"

    def get_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            ts_code = self._normalize_symbol(symbol)
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if df is None or df.empty:
                return pd.DataFrame()
            # 标准化字段
            df = df.rename(columns={
                "trade_date": "trade_date",
                "vol": "vol",
                "amount": "amount"
            })
            cols = ["trade_date", "open", "high", "low", "close", "vol", "amount"]
            df = df[[c for c in cols if c in df.columns]]
            df = df.sort_values("trade_date").reset_index(drop=True)
            return df
        except Exception:
            return pd.DataFrame()

    def get_minute(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        freq: str = "5min"
    ) -> pd.DataFrame:
        try:
            ts_code = self._normalize_symbol(symbol)

            # 兼容映射：3min 不支持，映射为 5min
            if freq == "3min":
                freq = "5min"

            # 转换日期格式为 Tushare 分钟接口需要的格式
            start_time = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]} 09:00:00"
            end_time = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]} 15:00:00"

            df = self.pro.stk_mins(
                ts_code=ts_code,
                freq=freq,
                start_time=start_time,
                end_time=end_time
            )
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(columns={"trade_time": "trade_date"})
            cols = ["trade_date", "open", "high", "low", "close", "vol", "amount"]
            df = df[[c for c in cols if c in df.columns]]
            df = df.sort_values("trade_date").reset_index(drop=True)
            return df
        except Exception:
            return pd.DataFrame()

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        try:
            ts_code = self._normalize_symbol(symbol)
            df = self.pro.stock_basic(ts_code=ts_code, fields="ts_code,name,industry,market,list_date")
            if df is None or df.empty:
                return {}
            return df.iloc[0].to_dict()
        except Exception:
            return {}
