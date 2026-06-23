import pandas as pd
from unittest.mock import patch, MagicMock

from eaagent.data_providers.tushare_stock import TushareStockProvider


class TestTushareStockProvider:

    def test_normalize_symbol(self):
        """测试股票代码自动补全后缀"""
        provider = TushareStockProvider(token="fake_token")

        assert provider._normalize_symbol("000001") == "000001.SZ"
        assert provider._normalize_symbol("600000") == "600000.SH"
        assert provider._normalize_symbol("000001.SZ") == "000001.SZ"
        assert provider._normalize_symbol("600000.SH") == "600000.SH"

    @patch("eaagent.data_providers.tushare_stock.ts.pro_api")
    def test_get_daily_success(self, mock_pro_api):
        """测试 get_daily 正常返回数据"""
        mock_df = pd.DataFrame({
            "trade_date": ["20250601", "20250602"],
            "open": [10.0, 10.2],
            "high": [10.5, 10.8],
            "low": [9.8, 10.0],
            "close": [10.3, 10.6],
            "vol": [100000, 120000],
            "amount": [1030000, 1272000],
        })

        mock_instance = MagicMock()
        mock_instance.daily.return_value = mock_df
        mock_pro_api.return_value = mock_instance

        provider = TushareStockProvider(token="fake_token")
        result = provider.get_daily("000001", "20250601", "20250602")

        assert not result.empty
        assert len(result) == 2
        assert "trade_date" in result.columns
        assert result.iloc[0]["close"] == 10.3

    @patch("eaagent.data_providers.tushare_stock.ts.pro_api")
    def test_get_daily_empty(self, mock_pro_api):
        """测试 get_daily 返回空数据时的情况"""
        mock_instance = MagicMock()
        mock_instance.daily.return_value = pd.DataFrame()
        mock_pro_api.return_value = mock_instance

        provider = TushareStockProvider(token="fake_token")
        result = provider.get_daily("000001", "20250601", "20250602")

        assert result.empty

    @patch("eaagent.data_providers.tushare_stock.ts.pro_api")
    def test_get_minute_success(self, mock_pro_api):
        """测试 get_minute 正常返回数据"""
        mock_df = pd.DataFrame({
            "trade_time": ["20250601 09:30:00", "20250601 09:35:00"],
            "open": [10.0, 10.1],
            "high": [10.2, 10.3],
            "low": [9.9, 10.0],
            "close": [10.1, 10.2],
            "vol": [5000, 6000],
            "amount": [50500, 61200],
        })

        mock_instance = MagicMock()
        mock_instance.stk_mins.return_value = mock_df
        mock_pro_api.return_value = mock_instance

        provider = TushareStockProvider(token="fake_token")
        result = provider.get_minute("000001", "20250601", "20250602", freq="5min")

        assert not result.empty
        assert len(result) == 2
        assert "trade_date" in result.columns

    @patch("eaagent.data_providers.tushare_stock.ts.pro_api")
    def test_get_symbol_info(self, mock_pro_api):
        """测试 get_symbol_info"""
        mock_df = pd.DataFrame({
            "ts_code": ["000001.SZ"],
            "name": ["平安银行"],
            "industry": ["银行"],
            "market": ["主板"],
            "list_date": ["19910403"],
        })

        mock_instance = MagicMock()
        mock_instance.stock_basic.return_value = mock_df
        mock_pro_api.return_value = mock_instance

        provider = TushareStockProvider(token="fake_token")
        info = provider.get_symbol_info("000001")

        assert info["ts_code"] == "000001.SZ"
        assert info["name"] == "平安银行"

    @patch("eaagent.data_providers.tushare_stock.ts.pro_api")
    def test_get_daily_exception_returns_empty(self, mock_pro_api):
        """测试接口抛异常时返回空 DataFrame"""
        mock_instance = MagicMock()
        mock_instance.daily.side_effect = Exception("API error")
        mock_pro_api.return_value = mock_instance

        provider = TushareStockProvider(token="fake_token")
        result = provider.get_daily("000001", "20250601", "20250602")

        assert result.empty

    @patch("eaagent.data_providers.tushare_stock.ts.pro_api")
    def test_get_symbol_info_exception_returns_empty(self, mock_pro_api):
        """测试 get_symbol_info 抛异常时返回空字典"""
        mock_instance = MagicMock()
        mock_instance.stock_basic.side_effect = Exception("API error")
        mock_pro_api.return_value = mock_instance

        provider = TushareStockProvider(token="fake_token")
        info = provider.get_symbol_info("000001")

        assert info == {}
