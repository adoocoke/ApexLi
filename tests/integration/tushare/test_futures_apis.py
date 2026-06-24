import pandas as pd
from datetime import datetime, timedelta


def get_recent_3m_dates():
    """获取最近3个月的日期范围"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")


class TestFuturesAPIs:

    def test_fut_basic(self, tushare_pro):
        """测试期货合约列表接口"""
        df = tushare_pro.fut_basic(exchange='', fut_type='1')
        assert isinstance(df, pd.DataFrame)
        if df.empty:
            print("⚠️ fut_basic 返回为空，可能是权限不足")

    def test_fut_daily(self, tushare_pro):
        """测试期货日线行情（使用当前活跃合约 + 最近3个月数据）"""
        start_date, end_date = get_recent_3m_dates()
        df = tushare_pro.fut_daily(
            ts_code='RB2609.SHF',           # 当前较活跃的合约
            start_date=start_date,
            end_date=end_date
        )
        assert isinstance(df, pd.DataFrame)
        if df.empty:
            print(f"⚠️ fut_daily 返回为空，合约: RB2609.SHF, 日期: {start_date} ~ {end_date}")

    def test_fut_holding(self, tushare_pro):
        """测试每日成交持仓排名"""
        df = tushare_pro.fut_holding(trade_date='20250410')
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

    def test_daily(self, tushare_pro):
        """测试个股日线数据"""
        df = tushare_pro.daily(
            ts_code='000001.SZ',
            start_date='20250401',
            end_date='20250410'
        )
        assert isinstance(df, pd.DataFrame)
        if df.empty:
            print("⚠️ daily 返回为空，可能是没有股票日线权限")

    def test_fund_daily(self, tushare_pro):
        """测试场内基金日线行情"""
        df = tushare_pro.fund_daily(
            ts_code='510300.SH',
            start_date='20250401',
            end_date='20250410'
        )
        assert isinstance(df, pd.DataFrame)
        if df.empty:
            print("⚠️ fund_daily 返回为空，可能是没有基金日线权限")
