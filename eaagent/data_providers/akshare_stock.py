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
            if "." not in code:
                if code.startswith("6"):
                    code = code + ".SH"
                else:
                    code = code + ".SZ"
            start = self._format_date(start_date)
            end = self._format_date(end_date)
            print(f"[Akshare] 请求日线: symbol={code}, start={start}, end={end}")

            # 临时清除代理环境变量，避免 ALL_PROXY 等干扰
            import os
            old_http = os.environ.pop("http_proxy", None)
            old_https = os.environ.pop("https_proxy", None)
            old_all = os.environ.pop("ALL_PROXY", None)
            old_http_upper = os.environ.pop("HTTP_PROXY", None)
            old_https_upper = os.environ.pop("HTTPS_PROXY", None)

            try:
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start,
                    end_date=end,
                    adjust="",
                    proxies={"http": None, "https": None},
                )
            finally:
                # 恢复环境变量
                if old_http is not None:
                    os.environ["http_proxy"] = old_http
                if old_https is not None:
                    os.environ["https_proxy"] = old_https
                if old_all is not None:
                    os.environ["ALL_PROXY"] = old_all
                if old_http_upper is not None:
                    os.environ["HTTP_PROXY"] = old_http_upper
                if old_https_upper is not None:
                    os.environ["HTTPS_PROXY"] = old_https_upper

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
            if "." not in code:
                if code.startswith("6"):
                    code = code + ".SH"
                else:
                    code = code + ".SZ"
            start = self._format_date(start_date)
            end = self._format_date(end_date)
            print(f"[Akshare] 请求分钟: symbol={code}, start={start}, end={end}, freq={freq}")

            # 临时清除代理环境变量
            import os
            old_http = os.environ.pop("http_proxy", None)
            old_https = os.environ.pop("https_proxy", None)
            old_all = os.environ.pop("ALL_PROXY", None)
            old_http_upper = os.environ.pop("HTTP_PROXY", None)
            old_https_upper = os.environ.pop("HTTPS_PROXY", None)

            try:
                df = ak.stock_zh_a_hist_min(
                    symbol=code,
                    period=freq,
                    start_date=start,
                    end_date=end,
                    adjust="qfq",
                    proxies={"http": None, "https": None},
                )
            finally:
                if old_http is not None:
                    os.environ["http_proxy"] = old_http
                if old_https is not None:
                    os.environ["https_proxy"] = old_https
                if old_all is not None:
                    os.environ["ALL_PROXY"] = old_all
                if old_http_upper is not None:
                    os.environ["HTTP_PROXY"] = old_http_upper
                if old_https_upper is not None:
                    os.environ["HTTPS_PROXY"] = old_https_upper

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
