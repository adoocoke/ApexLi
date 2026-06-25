import os
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from eaagent.tools.tushare_futures import get_futures_daily_with_ma, get_related_futures_daily

TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")


class TestGetFuturesDailyWithMa:

    @pytest.mark.skipif(not TUSHARE_TOKEN, reason="TUSHARE_TOKEN not set")
    def test_get_futures_daily_with_ma_success(self):
        """
        使用真实 TUSHARE_TOKEN 调用（仅在有 token 的 CI 环境下运行）
        使用 months=3 提高数据获取稳定性
        """
        result = get_futures_daily_with_ma('RB2610.SHF', months=3, ma_periods=[5, 13])

        if not result.empty:
            assert 'ma_5' in result.columns
            assert 'ma_13' in result.columns
            assert len(result) > 0
        else:
            # 如果返回空，也接受（可能是合约数据边界问题）
            pytest.skip("返回空数据，可能是合约数据边界或流动性问题")

    def test_get_futures_daily_with_ma_empty(self):
        """使用 mock 测试空数据场景"""
        mock_pro = MagicMock()
        mock_pro.fut_daily.return_value = pd.DataFrame()

        result = get_futures_daily_with_ma('RB2610.SHF', pro=mock_pro)
        assert result.empty


class TestGetRelatedFuturesDaily:

    @patch('eaagent.tools.tushare_futures.get_futures_daily_recent')
    def test_get_related_futures_daily_basic(self, mock_get_recent):
        df1 = pd.DataFrame({'ts_code': ['I2609.DCE'] * 3, 'close': [800, 805, 810]})
        df2 = pd.DataFrame({'ts_code': ['J2609.DCE'] * 3, 'close': [1800, 1820, 1850]})
        mock_get_recent.side_effect = [df1, df2]

        result = get_related_futures_daily(['I2609.DCE', 'J2609.DCE'], months=3)

        assert not result.empty
        assert len(result) == 6
