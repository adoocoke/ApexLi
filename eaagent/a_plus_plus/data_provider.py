import os
import pandas as pd
from typing import Dict, Any, List, Optional
from .config import DEFAULT_MOCK_DATA

MOCK_DAILY_CSV = "artifacts/mock_data/rb2605_fut_daily_2025.csv"


def get_historical_data(
    symbol: str = "RB2605.SHF",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_source: str = "mock"
) -> pd.DataFrame:
    """
    获取历史K线数据（自动兼容 RB2605 / RB2605.SHF 等写法）
    """
    if data_source != "mock":
        # 真实 Tushare 模式暂不处理（可后续扩展）
        return pd.DataFrame()

    if not os.path.exists(MOCK_DAILY_CSV):
        print(f"[Data] Mock CSV 文件不存在: {MOCK_DAILY_CSV}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(MOCK_DAILY_CSV)

        # 构造可能的 ts_code 变体（兼容不带后缀的情况）
        possible_codes = [symbol]
        if "." not in symbol:
            possible_codes.extend([
                f"{symbol}.SHF",
                f"{symbol}.DCE",
                f"{symbol}.CZC",
                f"{symbol}.INE"
            ])
        else:
            base = symbol.split(".")[0]
            possible_codes.append(base)

        possible_codes = list(set(possible_codes))

        # 尝试匹配
        matched_df = pd.DataFrame()
        for code in possible_codes:
            matched = df[df['ts_code'] == code]
            if not matched.empty:
                matched_df = matched
                print(f"[Data] 成功匹配到 ts_code: {code}")
                break

        if matched_df.empty:
            print(f"[Data] 未能在 CSV 中找到 {symbol} 及其变体")
            return pd.DataFrame()

        # 日期过滤
        if start_date:
            matched_df = matched_df[matched_df['trade_date'] >= start_date]
        if end_date:
            matched_df = matched_df[matched_df['trade_date'] <= end_date]

        return matched_df.sort_values('trade_date').reset_index(drop=True)

    except Exception as e:
        print(f"[Data] 读取 CSV 失败: {e}")
        return pd.DataFrame()


def get_mock_data(symbol: str = "RB2605.SHF") -> Dict[str, Any]:
    """返回Mock数据（优先从CSV取最新一条）"""
    df = get_historical_data(symbol, data_source="mock")
    if not df.empty:
        latest = df.iloc[-1]
        return {
            "5m": {
                "close": float(latest['close']),
                "volume": int(latest['vol']),
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
            },
            "30m": {
                "close": float(latest['close']),
                "volume": int(latest['vol']),
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
            },
            "1d": {
                "close": float(latest['close']),
                "volume": int(latest['vol']),
                "open": float(latest['open']),
                "high": float(latest['high']),
                "low": float(latest['low']),
            }
        }
    return DEFAULT_MOCK_DATA.copy()


def get_real_tushare_data(symbol: str, timeframes: List[str]) -> Dict[str, Any]:
    """获取真实 Tushare 数据"""
    print(f"[Tushare] 开始获取 {symbol} 的 {timeframes} 数据...")
    try:
        import tushare as ts
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("TUSHARE_TOKEN 环境变量未设置")

        ts.set_token(token)
        pro = ts.pro_api()

        data = {}
        for tf in timeframes:
            try:
                df = pro.fut_daily(ts_code=symbol, start_date='20250101', end_date='20250630')
                if not df.empty:
                    latest = df.iloc[0]
                    data[tf] = {
                        "close": float(latest['close']),
                        "volume": int(latest.get('vol', 0)),
                        "open": float(latest.get('open', 0)),
                        "high": float(latest.get('high', 0)),
                        "low": float(latest.get('low', 0)),
                    }
                    print(f"[Tushare] {tf} 获取成功 → close={data[tf]['close']}")
                else:
                    data[tf] = {"close": 0, "volume": 0}
                    print(f"[Tushare] {tf} 无数据")
            except Exception as e:
                data[tf] = {"close": 0, "volume": 0}
                print(f"[Tushare] {tf} 获取失败，原因: {str(e)}")
        return data

    except Exception as e:
        print(f"[Tushare] 整体获取失败，原因: {str(e)}，回退到 Mock 数据")
        return get_mock_data(symbol)


def get_market_data(data_source: str, symbol: str, timeframes: List[str]) -> Dict[str, Any]:
    """统一数据获取入口"""
    if data_source == "tushare":
        return get_real_tushare_data(symbol, timeframes)
    else:
        print("  → 使用增强 Mock 数据（来自CSV）")
        return get_mock_data(symbol)
