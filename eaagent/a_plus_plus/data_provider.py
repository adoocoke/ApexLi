"""
更新 data_provider.py 以支持从CSV加载更真实的Mock数据
请手动将以下内容合并到 eaagent/a_plus_plus/data_provider.py
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional
from .config import DEFAULT_MOCK_DATA, MAX_ROUNDS

MOCK_DAILY_CSV = "artifacts/mock_data/rb2605_fut_daily_2025.csv"


def get_mock_daily_data(
    symbol: str = "RB2605.SHF",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    从本地CSV文件加载Mock日线数据
    用于更真实的回测和模拟
    """
    if os.path.exists(MOCK_DAILY_CSV):
        try:
            df = pd.read_csv(MOCK_DAILY_CSV)
            df = df[df['ts_code'] == symbol].copy()
            
            if start_date:
                df = df[df['trade_date'] >= start_date]
            if end_date:
                df = df[df['trade_date'] <= end_date]
            
            df = df.sort_values('trade_date', ascending=False).reset_index(drop=True)
            return df
        except Exception as e:
            print(f"[Mock] 加载CSV失败: {e}，使用默认Mock数据")
    
    # Fallback: 返回空DataFrame
    return pd.DataFrame()


def get_mock_data(symbol: str = "RB2605.SHF") -> Dict[str, Any]:
    """
    返回Mock数据（优先从CSV加载最新一条）
    """
    df = get_mock_daily_data(symbol)
    
    if not df.empty:
        latest = df.iloc[0]
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
    
    # Fallback to simple default
    return DEFAULT_MOCK_DATA.copy()


def get_real_tushare_data(symbol: str, timeframes: List[str]) -> Dict[str, Any]:
    """获取真实 Tushare 数据（保持原有逻辑）"""
    print(f"[Tushare] 开始获取 {symbol} 的 {timeframes} 数据...")
    # ... 保持你原来的 Tushare 调用代码不变 ...
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
