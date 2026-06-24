from __future__ import annotations

from typing import Any, Dict, Optional
import pandas as pd
from eaagent.data_providers.base import DataProvider

try:
    import akshare as ak
except ImportError:
    ak = None


class AkshareStockProvider(DataProvider):
    """Akshare A股数据提供者实现"""

    def __init__(self, token: str | None = None, pro: Any = None):
        # Akshare 不需要 token/pro，保持接口一致
        self.pro = pro

    def _normalize_symbol(self, symbol: str) -> str:
        """去除后缀，返回纯代码"""
        if "." in symbol:
            return symbol.split(".")[0]
        return symbol

    def _format_date(self, date_str: str) -> str:
        """将 YYYYMMDD 转为 YYYY-MM-DD"""
        if not date_str:
            return date_str
        if "-" in date_str:
            return date_str
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        return date_str

    def get_daily(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        if ak is None:
            return pd.DataFrame()
        try:
            code = self._normalize_symbol(symbol)
            # 强制把 YYYYMMDD 转为 YYYY-MM-DD
            start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
            end_date   = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
            print(f"[Akshare] 请求日线: symbol={code}, start={start_date}, end={end_date}, adjust=''")
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="",
            )
            row_count = len(df) if df is not None else 0
            print(f"[Akshare] 返回行数: {row_count}")
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(
                columns={
                    "日期": "trade_date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "vol",
                    "成交额": "amount",
                }
            )
            return df[["trade_date", "open", "high", "low", "close", "vol", "amount"]]
        except Exception:
            return pd.DataFrame()

    def get_minute(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        freq: str = "5min",
    ) -> pd.DataFrame:
        if ak is None:
            return pd.DataFrame()
        try:
            code = self._normalize_symbol(symbol)
            start = self._format_date(start_date)
            end = self._format_date(end_date)
            print(f"[Akshare] 请求分钟: symbol={code}, start={start}, end={end}, freq={freq}")
            df = ak.stock_zh_a_hist_min(
                symbol=code,
                period=freq,
                start_date=start,
                end_date=end,
                adjust="",
            )
            row_count = len(df) if df is not None else 0
            print(f"[Akshare] 返回行数: {row_count}")
            if df is None or df.empty:
                return pd.DataFrame()
            df = df.rename(
                columns={
                    "时间": "trade_date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "vol",
                    "成交额": "amount",
                }
            )
            return df[["trade_date", "open", "high", "low", "close", "vol", "amount"]]
        except Exception:
            return pd.DataFrame()

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        return {}
