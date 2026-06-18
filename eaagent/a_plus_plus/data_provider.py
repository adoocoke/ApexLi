"""数据获取模块（Mock + 真实 Tushare）"""

import os
from typing import Dict, Any, List
from .config import DEFAULT_MOCK_DATA


def get_mock_data() -> Dict[str, Any]:
    """返回 Mock 数据"""
    return DEFAULT_MOCK_DATA.copy()


def get_real_tushare_data(symbol: str, timeframes: List[str]) -> Dict[str, Any]:
    """获取真实 Tushare 数据（带详细日志和降级）"""
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
                df = pro.fut_daily(ts_code=symbol, start_date='20240601', end_date='20240618')
                if not df.empty:
                    latest = df.iloc[-1]
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
                    print(f"[Tushare] {tf} 无数据，原因: 该时间段内无交易记录或品种代码错误")
            except Exception as e:
                data[tf] = {"close": 0, "volume": 0}
                print(f"[Tushare] {tf} 获取失败，具体原因: {str(e)}")

        return data

    except Exception as e:
        print(f"[Tushare] 整体获取失败，原因: {str(e)}，回退到 Mock 数据")
        return get_mock_data()


def get_market_data(data_source: str, symbol: str, timeframes: List[str]) -> Dict[str, Any]:
    """统一数据获取入口"""
    if data_source == "tushare":
        return get_real_tushare_data(symbol, timeframes)
    else:
        print("  → 使用 Mock 数据")
        return get_mock_data()
