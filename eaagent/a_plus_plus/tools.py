import os
import pandas as pd
from typing import Optional, Dict, Any, Literal
from dotenv import load_dotenv

import tushare as ts

load_dotenv()

_pro_api = None


def get_pro_api():
    """获取 Tushare Pro API（单例模式）"""
    global _pro_api
    if _pro_api is None:
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("TUSHARE_TOKEN 未在 .env 中配置")
        ts.set_token(token)
        _pro_api = ts.pro_api()
    return _pro_api


def _normalize_ts_code(symbol: str, exchange: str = "SHF") -> str:
    """自动补全 ts_code"""
    symbol = symbol.upper().strip()
    if "." in symbol:
        return symbol
    return f"{symbol}.{exchange}"


def get_futures_klines(
    symbol: str,
    period: Literal["D", "60", "30", "15", "5"] = "D",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 300,
    exchange: str = "SHF"
) -> pd.DataFrame:
    """
    获取期货K线数据（参考 Tushare 官方文档）
    """
    pro = get_pro_api()
    ts_code = _normalize_ts_code(symbol, exchange)

    try:
        if period == "D":
            df = pro.fut_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        else:
            freq_map = {"60": "60min", "30": "30min", "15": "15min", "5": "5min"}
            freq = freq_map.get(period, "60min")
            df = pro.fut_min(
                ts_code=ts_code,
                freq=freq,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
    except Exception as e:
        print(f"[Tushare Error] 获取 {ts_code} 数据失败: {e}")
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    # 统一按时间排序
    date_col = "trade_date" if "trade_date" in df.columns else "datetime"
    df = df.sort_values(date_col).reset_index(drop=True)
    return df


def calculate_volume_oi_change(df: pd.DataFrame) -> Dict[str, Any]:
    """计算成交量和持仓量变化（核心量仓逻辑）"""
    if df.empty or len(df) < 2:
        return {
            "volume_change": 0,
            "oi_change": 0,
            "volume_change_pct": 0,
            "summary": "数据不足，无法计算量仓变化"
        }

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    vol_change = int(latest.get("vol", 0) - prev.get("vol", 0))
    oi_change = int(latest.get("oi", 0) - prev.get("oi", 0))
    vol_pct = round(vol_change / max(prev.get("vol", 1), 1) * 100, 1)

    return {
        "volume_change": vol_change,
        "oi_change": oi_change,
        "volume_change_pct": vol_pct,
        "summary": f"成交量变化 {vol_change:+d} ({vol_pct:+.1f}%), 持仓量变化 {oi_change:+d}"
    }


def get_latest_observation(
    symbol: str,
    period: Literal["D", "60", "30", "15", "5"] = "D",
    lookback: int = 5,
    exchange: str = "SHF"
) -> str:
    """
    返回结构化的量仓 + 价格观察（最适合给 ReAct Agent 使用）
    """
    df = get_futures_klines(
        symbol=symbol,
        period=period,
        limit=lookback + 3,
        exchange=exchange
    )

    if df.empty:
        return f"【{symbol}】无法获取数据，请检查合约代码、交易所或 Tushare 期货权限。"

    vol_oi = calculate_volume_oi_change(df)
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    close = latest.get("close", 0)
    pre_close = prev.get("close", close)
    price_chg = round(close - pre_close, 2)
    price_pct = round(price_chg / pre_close * 100, 2) if pre_close > 0 else 0

    obs = f"""【{symbol} 最新观察】
- 最新收盘价: {close}
- 价格变化: {price_chg:+.2f} ({price_pct:+.2f}%)
- {vol_oi['summary']}
- 最近 {len(df)} 根K线数据"""
    return obs.strip()


if __name__ == "__main__":
    # 测试
    print(get_latest_observation("I2409", period="D"))
    print("=" * 60)
    print(get_latest_observation("RB2405", period="D"))
