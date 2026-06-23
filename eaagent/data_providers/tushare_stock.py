import pandas as pd
from typing import Any, Dict, Optional
from datetime import datetime

from .base import DataProvider


class TushareStockProvider(DataProvider):
    """Tushare A股数据提供者实现"""

    def __init__(self, token: str | None = None, pro: Any = None):
        if pro is not None:
            self.pro = pro
        else:
            import tushare as ts
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
            df = self.pro.stk_mins(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date
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
