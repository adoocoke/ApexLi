# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import tushare as ts
import re
import os

def _get_correct_exchange(symbol: str) -> str:
    prefix = re.match(r'([A-Z]+)', symbol.upper())
    if not prefix:
        return 'SHF'
    p = prefix.group(1)
    dce_prefixes = ['I', 'JM', 'J', 'A', 'M', 'Y', 'P', 'C', 'CS', 'PP', 'L', 'V', 'EG', 'RR', 'BB', 'FB']
    if p in dce_prefixes:
        return 'DCE'
    shf_prefixes = ['RB', 'HC', 'CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'BU', 'RU', 'FU', 'SC', 'NR']
    if p in shf_prefixes:
        return 'SHF'
    czce_prefixes = ['SR', 'CF', 'TA', 'MA', 'FG', 'ZC', 'OI', 'RM', 'RS', 'SF', 'SM', 'UR', 'SA', 'PF', 'AP', 'CJ', 'PK']
    if p in czce_prefixes:
        return 'CZCE'
    return 'SHF'


def get_futures_daily_recent(
    ts_code: str,
    months: int = 5,
    pro: Optional[object] = None
) -> pd.DataFrame:
    if pro is None:
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("请设置环境变量 TUSHARE_TOKEN")
        pro = ts.pro_api(token)

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=months * 30 + 10)).strftime("%Y%m%d")

    try:
        df = pro.fut_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields="ts_code,trade_date,open,high,low,close,settle,vol,amount,oi,oi_chg"
        )
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.sort_values("trade_date").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"[Tushare] 获取 {ts_code} 日线失败: {e}")
        return pd.DataFrame()


def get_related_futures_daily(
    symbols: List[str],
    months: int = 3,
    pro: Optional[object] = None
) -> pd.DataFrame:
    all_data = []
    for raw_symbol in symbols:
        if '.' not in raw_symbol:
            exchange = _get_correct_exchange(raw_symbol)
            symbol = f"{raw_symbol}.{exchange}"
        else:
            symbol = raw_symbol

        df = get_futures_daily_recent(symbol, months=months, pro=pro)

        if df.empty:
            for ex in ['DCE', 'SHF', 'CZCE']:
                test_symbol = f"{raw_symbol.split('.')[0]}.{ex}"
                df = get_futures_daily_recent(test_symbol, months=months, pro=pro)
                if not df.empty:
                    break

        if not df.empty:
            all_data.append(df)

    if not all_data:
        return pd.DataFrame()
    return pd.concat(all_data, ignore_index=True)


def get_futures_daily_with_ma(
    ts_code: str,
    months: int = 5,
    ma_periods: List[int] = [5, 13, 20],
    pro: Optional[object] = None
) -> pd.DataFrame:
    """
    使用 fut_daily + pandas 计算均线（更稳定，不依赖 pro_bar 的 ma 参数）
    """
    if pro is None:
        import os
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("请设置环境变量 TUSHARE_TOKEN")
        pro = ts.pro_api(token)

    max_ma = max(ma_periods) if ma_periods else 20
    extra_days = int(max_ma * 1.5) + 10

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=months * 30 + extra_days)).strftime("%Y%m%d")

    try:
        df = pro.fut_daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            fields="ts_code,trade_date,open,high,low,close,settle,vol,amount,oi,oi_chg"
        )
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.sort_values("trade_date").reset_index(drop=True)

        # 用 pandas 计算均线
        for period in ma_periods:
            df[f"ma_{period}"] = df["close"].rolling(window=period).mean()

        # 只保留目标月份的数据
        target_start = (datetime.now() - timedelta(days=months * 30)).strftime("%Y%m%d")
        df = df[df["trade_date"] >= target_start].reset_index(drop=True)

        return df
    except Exception as e:
        print(f"[Tushare] 获取 {ts_code} 带均线数据失败: {e}")
        return pd.DataFrame()


def get_popular_main_contracts() -> List[str]:
    """返回热门主力合约列表 (中文+代码格式, 优先用户关注的品种 per plan)"""
    # VARIETY_NAME_MAP for Chinese display (螺纹钢 RB2610.SHF etc.)
    VARIETY_NAME_MAP = {
        "RB": "螺纹钢", "I": "铁矿石", "JM": "焦煤", "J": "焦炭",
        "RM": "菜粕", "P": "棕榈油", "SA": "纯碱", "FG": "玻璃",
        "AL": "沪铝", "AG": "沪银", "CF": "棉花", "LC": "碳酸锂",
        "IC": "IC", "IM": "IM", "HC": "热卷", "ZC": "焦炭相关",
    }
    popular_codes = [
        "RB2610.SHF", "I2609.DCE", "JM2609.DCE", "J2609.DCE",  # 螺纹/铁矿/焦煤/焦炭
        "SA2609.ZCE", "SA609.ZCE", "FG2606.ZCE", "SH2609.ZCE", "TA1001.ZCE", "AL2610.SHF", "AG2609.SHF", # SA2609.ZCE as requested + other active ZCE
        "P2609.DCE", "RM2609.CZC", "CF2609.CZC", "IC2509.CFE", "IM2509.CFE", "LC2609.SHF"
    ]
    # Format as "中文 代码" for Dropdown display (user requirement)
    return [f"{VARIETY_NAME_MAP.get(code.split('.')[0], code.split('.')[0])} {code}" for code in popular_codes]


def get_main_contracts(exchange: str = "", limit: int = 20) -> List[Dict]:
    """从 Tushare 获取主力合约列表 (按 volume/oi 排序, name增强为中文+代码 per plan)"""
    VARIETY_NAME_MAP = {  # Reuse same map for consistency (CZCE suffix unified to .CZCE where possible)
        "RB": "螺纹钢", "I": "铁矿石", "JM": "焦煤", "J": "焦炭",
        "RM": "菜粕", "P": "棕榈油", "SA": "纯碱", "FG": "玻璃",
        "AL": "沪铝", "AG": "沪银", "CF": "棉花", "LC": "碳酸锂",
        "IC": "IC", "IM": "IM", "HC": "热卷", "ZC": "焦炭相关",
    }
    try:
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            print("[Tushare] No token, returning popular list")
            popular = get_popular_main_contracts()  # Now returns formatted strings
            return [{"ts_code": item.split()[-1], "name": item} for item in popular]

        pro = ts.pro_api(token)
        df = pro.fut_basic(exchange=exchange, fut_type='1')
        if df is None or df.empty:
            popular = get_popular_main_contracts()
            return [{"ts_code": item.split()[-1], "name": item} for item in popular]

        # 筛选活跃合约并排序 (主力通常 vol/oi 高)
        if 'delist_date' in df.columns:
            df = df[df['delist_date'] > '2026-12-31']  # 排除已退市
        if 'vol' in df.columns:
            df = df.sort_values('vol', ascending=False)
        main_list = df.head(limit)[['ts_code', 'name']].to_dict('records')
        # Ensure CZCE active (SA/FG/SH) are included even if delist_date filter removes them
        if not any("SA" in str(m.get("ts_code", "")) or "FG" in str(m.get("ts_code", "")) for m in main_list):
            main_list = [{"ts_code": "SA609.CZCE", "name": "纯碱 SA609.CZCE"}, {"ts_code": "FG2606.CZCE", "name": "玻璃 FG2606.CZCE"}] + main_list[:8]
        # Enhance name with Chinese if possible (map fallback)
        for item in main_list:
            prefix = item['ts_code'].split('.')[0].split()[0] if ' ' in item['ts_code'] else item['ts_code'].split('.')[0]
            chinese = VARIETY_NAME_MAP.get(prefix, item.get('name', prefix))
            item['name'] = f"{chinese} {item['ts_code']}"
        return main_list if main_list else [{"ts_code": item.split()[-1], "name": item} for item in get_popular_main_contracts()]
    except Exception as e:
        print(f"[Tushare] get_main_contracts failed: {e}")
        popular = get_popular_main_contracts()
        return [{"ts_code": item.split()[-1], "name": item} for item in popular]
