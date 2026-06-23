from __future__ import annotations

from eaagent.data_providers.base import DataProvider
from eaagent.data_providers.tushare_futures import TushareFuturesProvider
from eaagent.data_providers.tushare_stock import TushareStockProvider
from eaagent.data_providers.akshare_stock import AkshareStockProvider


def get_data_provider(
    name: str = "tushare_futures", 
    **kwargs
) -> DataProvider:
    """
    数据提供者工厂方法

    Args:
        name: 数据提供者名称，目前支持：
              - "tushare_futures" (默认)
              - "tushare_stock"
              - "akshare_stock"
        **kwargs: 传递给具体 Provider 的参数（如 token）

    Returns:
        DataProvider 实例
    """
    if name == "tushare_futures":
        return TushareFuturesProvider(**kwargs)
    elif name == "tushare_stock":
        return TushareStockProvider(**kwargs)
    elif name == "akshare_stock":
        return AkshareStockProvider(**kwargs)
    else:
        raise ValueError(
            f"Unknown data provider: '{name}'. "
            f"Currently supported: 'tushare_futures', 'tushare_stock', 'akshare_stock'"
        )
