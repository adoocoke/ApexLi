from __future__ import annotations

import pandas as pd
import tushare as ts
from typing import Dict, Any

from eaagent.data_providers.base import DataProvider


class TushareFuturesProvider(DataProvider):
    """Tushare 期货数据提供者实现"""

    def __init__(self, token: str | None = None):
        if token:
            ts.set_token(token)
        self.pro = ts.pro_api()

    def _normalize_symbol(self, symbol: str) -> str:
        """将 RB2605 转换为 RB2605.SHF"""
        if "." in symbol:
            return symbol
        # 常见期货品种后缀映射（可扩展）
        suffix_map = {
            "RB": "SHF",   # 螺纹钢
            "HC": "SHF",   # 热卷
            "I":  "DCE",   # 铁矿石
            "J":  "DCE",   # 焦炭
            "JM": "DCE",   # 焦煤
            "M":  "DCE",   # 豆粕
            "Y":  "DCE",   # 豆油
            "P":  "DCE",   # 棕榈油
            "SA": "CZC",   # 纯碱
            # 可继续补充
        }
        for prefix, suffix in suffix_map.items():
            if symbol.upper().startswith(prefix):
                return f"{symbol.upper()}.{suffix}"
        return symbol.upper()

    def get_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        ts_code = self._normalize_symbol(symbol)
        try:
            df = self.pro.fut_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if df.empty:
                return df

            # 标准化字段
            df = df.rename(columns={
                "trade_date": "trade_date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "vol",
                "amount": "amount",
                "oi": "oi",
            })
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df = df.sort_values("trade_date").reset_index(drop=True)
            return df

        except Exception as e:
            print(f"[TushareFuturesProvider] get_daily 失败: {e}")
            return pd.DataFrame()

    def get_minute(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        freq: str = "5min"
    ) -> pd.DataFrame:
        ts_code = self._normalize_symbol(symbol)
        try:
            df = self.pro.fut_min(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                freq=freq
            )
            if df.empty:
                return df

            df = df.rename(columns={
                "trade_time": "trade_time",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "vol": "vol",
                "amount": "amount",
                "oi": "oi",
            })
            df["trade_time"] = pd.to_datetime(df["trade_time"])
            df = df.sort_values("trade_time").reset_index(drop=True)
            return df

        except Exception as e:
            print(f"[TushareFuturesProvider] get_minute 失败: {e}")
            return pd.DataFrame()

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """简单返回标的基本信息（可后续扩展从 fut_basic 获取）"""
        return {
            "symbol": symbol,
            "normalized_symbol": self._normalize_symbol(symbol),
            "market": "futures",
            "provider": "tushare"
        }
