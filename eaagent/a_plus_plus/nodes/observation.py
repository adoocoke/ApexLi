from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
import json
import pandas as pd
from typing import List, Dict, Any

def _prepare_daily_data(daily_data: List[Dict[str, Any]], max_rows: int = 60) -> str:
    """准备发给 LLM 的日线数据，包含 oi_chg"""
    if not daily_data:
        return ""
    df = pd.DataFrame(daily_data)
    keep_cols = ["trade_date", "open", "high", "low", "close", "vol", "amount", "oi", "oi_chg"]
    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols].tail(max_rows)
    return df.to_csv(index=False)

def structured_observation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 结构化市场观察", Colors.OKCYAN)

    daily_data = state.get("market_data", {}).get("daily_df", [])
    if not daily_data:
        # 保持原有空数据处理逻辑
        obs_data = {
            "phase": "数据缺失",
            "trend": {"mid_term": "数据缺失", "short_term": "数据缺失"},
            "key_levels": {"strong_resistance": [], "strong_support": []},
            "volume_analysis": "数据缺失",
            "oi_analysis": "数据缺失",
            "pattern": "数据缺失",
            "conclusion": "历史数据为空，无法进行有效技术分析。",
            "risk_note": "数据不足",
            "playbook_references": []
        }
        state["observations"].append(obs_data)
        return state

    data_str = _prepare_daily_data(daily_data)

    prompt = f"""以下是 {state['current_symbol']} 最近的日线数据（包含 oi_chg 持仓量变化）：

{data_str}

请基于以上数据进行专业的技术分析，并严格按照以下 JSON 格式返回（不要有任何额外文字）：

{{
  "phase": "当前所处阶段（例如：下跌中继 / 筑底反弹 / 趋势反转 / 高位震荡 等）",
  "trend": {{
    "mid_term": "中线趋势判断",
    "short_term": "短线趋势判断"
  }},
  "key_levels": {{
    "strong_resistance": ["价位1", "价位2"],
    "strong_support": ["价位1", "价位2"]
  }},
  "volume_analysis": "对成交量变化的分析（是否放量、缩量、量价配合情况）",
  "oi_analysis": "对持仓量变化的分析（重点关注 oi_chg 的正负和幅度，判断多空增减仓情况）",
  "pattern": "当前形态（例如：下跌通道、V型反转、平台整理等）",
  "conclusion": "综合结论和交易倾向",
  "risk_note": "主要风险点",
  "playbook_references": ["引用的 Playbook 规则名称"]
}}"""

    system_prompt = state["messages"][0]["content"] if state.get("messages") else ""
    from eaagent.a_plus_plus.utils.llm import call_llm
    response = call_llm(prompt, system_prompt)

    try:
        obs_data = json.loads(response)
    except json.JSONDecodeError:
        obs_data = {
            "phase": "解析失败",
            "trend": {"mid_term": "解析失败", "short_term": "解析失败"},
            "key_levels": {"strong_resistance": [], "strong_support": []},
            "volume_analysis": "解析失败",
            "oi_analysis": "解析失败",
            "pattern": "解析失败",
            "conclusion": response[:600],
            "risk_note": "LLM 返回格式异常",
            "playbook_references": []
        }

    state["observations"].append(obs_data)
    return state
