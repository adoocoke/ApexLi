import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from eaagent.tools.tushare_futures import (
    get_related_futures_daily,
    get_futures_daily_with_ma
)


class TestGetRelatedFuturesDaily:
    @patch('eaagent.tools.tushare_futures.get_futures_daily_recent')
    def test_get_related_futures_daily_basic(self, mock_get_recent):
        # 模拟返回两个品种的数据
        df1 = pd.DataFrame({'ts_code': ['I2609.SHF'] * 3, 'close': [800, 805, 810]})
        df2 = pd.DataFrame({'ts_code': ['J2609.SHF'] * 3, 'close': [1800, 1820, 1850]})
        mock_get_recent.side_effect = [df1, df2]

        result = get_related_futures_daily(['I2609.SHF', 'J2609.SHF'], months=3)

        assert not result.empty
        assert len(result) == 6
        assert set(result['ts_code'].unique()) == {'I2609.SHF', 'J2609.SHF'}


class TestGetFuturesDailyWithMa:
    @patch('tushare.pro_api')
    def test_get_futures_daily_with_ma_calls_pro_bar(self, mock_pro_api):
        mock_pro = MagicMock()
        mock_df = pd.DataFrame({
            'ts_code': ['RB2610.SHF'] * 5,
            'trade_date': ['20260620', '20260619', '20260618', '20260617', '20260616'],
            'close': [3120, 3135, 3080, 3150, 3200],
            'ma_5': [3110, 3120, 3100, 3140, 3180],
            'ma_13': [3100, 3115, 3090, 3130, 3170]
        })
        mock_pro.pro_bar.return_value = mock_df
        mock_pro_api.return_value = mock_pro

        result = get_futures_daily_with_ma('RB2610.SHF', months=1, ma_periods=[5, 13])

        assert not result.empty
        assert 'ma_5' in result.columns
        assert 'ma_13' in result.columns
        mock_pro.pro_bar.assert_called_once()
