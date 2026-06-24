import pandas as pd
from unittest.mock import patch, MagicMock
import pytest

from eaagent.data_providers.tushare_futures import TushareFuturesProvider


class TestTushareFuturesProvider:

    def test_normalize_symbol(self):
        """测试品种代码自动补全后缀"""
        provider = TushareFuturesProvider(token="fake_token")

        assert provider._normalize_symbol("RB2605") == "RB2605.SHF"
        assert provider._normalize_symbol("RB2605.SHF") == "RB2605.SHF"
        assert provider._normalize_symbol("I2509") == "I2509.DCE"
        assert provider._normalize_symbol("SA2601") == "SA2601.CZC"
        assert provider._normalize_symbol("999999") == "999999"  # 未知品种保持原样

    @patch("eaagent.data_providers.tushare_futures.ts.pro_api")
    def test_get_daily_success(self, mock_pro_api):
        """测试 get_daily 正常返回数据"""
        # 构造 mock 返回数据
        mock_df = pd.DataFrame({
            "trade_date": ["20250601", "20250602"],
            "open": [4100, 4120],
            "high": [4150, 4180],
            "low": [4080, 4100],
            "close": [4125, 4155],
            "vol": [120000, 135000],
            "oi": [180000, 185000],
        })

        mock_instance = MagicMock()
        mock_instance.fut_daily.return_value = mock_df
        mock_pro_api.return_value = mock_instance

        provider = TushareFuturesProvider(token="fake_token")
        result = provider.get_daily("RB2605", "20250601", "20250602")

        assert not result.empty
        assert len(result) == 2
        assert "trade_date" in result.columns
        assert result.iloc[0]["close"] == 4125

    @patch("eaagent.data_providers.tushare_futures.ts.pro_api")
    def test_get_daily_empty(self, mock_pro_api):
        """测试 get_daily 返回空数据时的情况"""
        mock_instance = MagicMock()
        mock_instance.fut_daily.return_value = pd.DataFrame()
        mock_pro_api.return_value = mock_instance

        provider = TushareFuturesProvider(token="fake_token")
        result = provider.get_daily("RB2605", "20250601", "20250602")

        assert result.empty

    @patch("eaagent.data_providers.tushare_futures.ts.pro_api")
    def test_get_symbol_info(self, mock_pro_api):
        """测试 get_symbol_info"""
        provider = TushareFuturesProvider(token="fake_token")
        info = provider.get_symbol_info("RB2605")

        assert info["symbol"] == "RB2605"
        assert info["normalized_symbol"] == "RB2605.SHF"
        assert info["market"] == "futures"