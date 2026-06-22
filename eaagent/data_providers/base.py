from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any


class DataProvider(ABC):
    """数据提供者抽象基类

    所有具体数据源（期货、股票等）都需要实现此接口。
    """

    @abstractmethod
    def get_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线数据"""
        pass

    @abstractmethod
    def get_minute(
        self, symbol: str, start_date: str, end_date: str, freq: str = "5min"
    ) -> pd.DataFrame:
        """获取分钟线数据"""
        pass

    @abstractmethod
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """获取标的物基本信息"""
        pass
