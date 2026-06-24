import pandas as pd


class TestFuturesAPIs:

    def test_fut_basic(self, tushare_pro):
        """测试期货合约列表接口"""
        df = tushare_pro.fut_basic(exchange='', fut_type='1')
        assert isinstance(df, pd.DataFrame)
        # 允许为空（部分账号可能没权限）
        if df.empty:
            print("⚠️ fut_basic 返回为空，可能是权限不足")

    def test_fut_daily(self, tushare_pro):
        """测试期货日线行情"""
        df = tushare_pro.fut_daily(
            ts_code='RB2505.SHF',
            start_date='20250401',
            end_date='20250410'
        )
        assert isinstance(df, pd.DataFrame)
        if df.empty:
            print("⚠️ fut_daily 返回为空，可能是权限不足或合约已到期")

    def test_fut_holding(self, tushare_pro):
        """测试每日成交持仓排名"""
        df = tushare_pro.fut_holding(
            ts_code='RB2505.SHF',
            start_date='20250401',
            end_date='20250410'
        )
        assert isinstance(df, pd.DataFrame)

    def test_fut_wsr(self, tushare_pro):
        """测试仓单日报"""
        df = tushare_pro.fut_wsr(trade_date='20250410')
        assert isinstance(df, pd.DataFrame)

    def test_fut_settle(self, tushare_pro):
        """测试结算参数"""
        df = tushare_pro.fut_settle(trade_date='20250410')
        assert isinstance(df, pd.DataFrame)

    def test_trade_cal(self, tushare_pro):
        """测试交易日历"""
        df = tushare_pro.trade_cal(
            start_date='20250401',
            end_date='20250410'
        )
        assert isinstance(df, pd.DataFrame)
        if df.empty:
            print("⚠️ trade_cal 返回为空，可能是权限不足")
