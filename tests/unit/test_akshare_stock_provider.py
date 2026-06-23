import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from eaagent.data_providers.akshare_stock import AkshareStockProvider


class TestAkshareStockProvider:

    def test_get_daily_normal(self):
        provider = AkshareStockProvider()
        mock_df = pd.DataFrame({
            "日期": ["2024-01-01"],
            "开盘": [10.0],
            "最高": [11.0],
            "最低": [9.5],
            "收盘": [10.5],
            "成交量": [100000],
            "成交额": [1050000],
        })
        with patch("eaagent.data_providers.akshare_stock.ak.stock_zh_a_hist", return_value=mock_df):
            result = provider.get_daily("000001.SZ", "20240101", "20240102")
            assert not result.empty
            assert "trade_date" in result.columns

    def test_get_daily_empty(self):
        provider = AkshareStockProvider()
        with patch("eaagent.data_providers.akshare_stock.ak.stock_zh_a_hist", return_value=pd.DataFrame()):
            result = provider.get_daily("000001.SZ", "20240101", "20240102")
            assert result.empty

    def test_get_minute_normal(self):
        provider = AkshareStockProvider()
        mock_df = pd.DataFrame({
            "时间": ["2024-01-01 09:30"],
            "开盘": [10.0],
            "最高": [10.1],
            "最低": [9.9],
            "收盘": [10.05],
            "成交量": [5000],
            "成交额": [50250],
        })
        with patch("eaagent.data_providers.akshare_stock.ak.stock_zh_a_hist_min", return_value=mock_df):
            result = provider.get_minute("000001.SZ", "20240101", "20240102", freq="5min")
            assert not result.empty
            assert "trade_date" in result.columns

    def test_get_daily_exception_returns_empty(self):
        provider = AkshareStockProvider()
        with patch("eaagent.data_providers.akshare_stock.ak.stock_zh_a_hist", side_effect=Exception("boom")):
            result = provider.get_daily("000001.SZ", "20240101", "20240102")
            assert result.empty

    def test_normalize_symbol(self):
        provider = AkshareStockProvider()
        assert provider._normalize_symbol("000001.SZ") == "000001"
        assert provider._normalize_symbol("600000") == "600000"
