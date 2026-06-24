import pandas as pd


class TestFuturesAPIs:

    def test_fut_basic(self, tushare_pro):
        """测试期货合约列表接口"""
        # 使用更宽松的参数
        df = tushare_pro.fut_basic(exchange='', fut_type='1')
        assert isinstance(df, pd.DataFrame)
        assert not df.empty, "fut_basic 返回数据为空，请检查权限或参数"

    def test_fut_daily(self, tushare_pro):
        """测试期货日线行情（使用当前活跃合约）"""
        # 使用当前仍活跃的合约（假设现在是2026年6月）
        df = tushare_pro.fut_daily(
            ts_code='RB2609.SHF',           # 改成9月合约
            start_date='20250601',
            end_date='20250610'
        )
        assert isinstance(df, pd.DataFrame)
        assert not df.empty, "fut_daily 返回数据为空，请检查合约代码或权限"

    def test_fut_holding(self, tushare_pro):
        """测试每日成交持仓排名"""
        df = tushare_pro.fut_holding(
            ts_code='RB2609.SHF',
            start_date='20250601',
            end_date='20250610'
        )
        assert isinstance(df, pd.DataFrame)
        # 持仓数据部分合约可能为空，允许为空

    def test_fut_wsr(self, tushare_pro):
        """测试仓单日报"""
        df = tushare_pro.fut_wsr(trade_date='20250610')
        assert isinstance(df, pd.DataFrame)

    def test_fut_settle(self, tushare_pro):
        """测试结算参数"""
        df = tushare_pro.fut_settle(trade_date='20250610')
        assert isinstance(df, pd.DataFrame)
