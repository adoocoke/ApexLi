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
        df1 = pd.DataFrame({'ts_code': ['I2609.DCE'] * 3, 'close': [800, 805, 810]})
        df2 = pd.DataFrame({'ts_code': ['J2609.DCE'] * 3, 'close': [1800, 1820, 1850]})
        mock_get_recent.side_effect = [df1, df2]

        result = get_related_futures_daily(['I2609.DCE', 'J2609.DCE'], months=3)

        assert not result.empty
        assert len(result) == 6


class TestGetFuturesDailyWithMa:
    @patch('tushare.pro_api')
    def test_get_futures_daily_with_ma_success(self, mock_pro_api):
        """测试 get_futures_daily_with_ma 能正确调用 fut_daily 并计算均线"""
        mock_pro = MagicMock()
        mock_df = pd.DataFrame({
            'ts_code': ['RB2610.SHF'] * 10,
            'trade_date': [f'202606{str(i).zfill(2)}' for i in range(15, 25)],
            'close': [3120, 3135, 3080, 3150, 3200, 3180, 3165, 3140, 3110, 3095]
        })
        mock_pro.fut_daily.return_value = mock_df
        mock_pro_api.return_value = mock_pro

        result = get_futures_daily_with_ma('RB2610.SHF', months=1, ma_periods=[5, 13])

        assert not result.empty
        assert 'ma_5' in result.columns
        assert 'ma_13' in result.columns
        # 验证调用的是 fut_daily 而不是 pro_bar
        mock_pro.fut_daily.assert_called_once()
