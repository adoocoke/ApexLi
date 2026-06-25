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
        obs_data = {
            "phase": "数据缺失",
            "trend": {"mid_term": "数据缺失", "short_term": "数据缺失"},
            "key_levels": {"strong_resistance": [], "strong_support": []},
            "volume_oi_linkage": "数据缺失",
            "key_events": [],
            "force_comparison": "数据缺失",
            "trading_bias": "数据缺失",
            "main_contradiction": "数据缺失",
            "playbook_references": []
        }
        state["observations"].append(obs_data)
        return state

    data_str = _prepare_daily_data(daily_data)

    prompt = f"""以下是 {state['current_symbol']} 最近的日线数据（包含成交量、持仓量及持仓变化 oi_chg）：

{data_str}

请基于以上完整数据进行专业、系统化的技术分析，并**严格按照以下 JSON 格式**返回结果（不要有任何额外文字说明）：

{{
  "phase": "当前所处阶段（例如：下跌中继、筑底反弹、趋势反转、高位震荡等）",
  "trend": {{
    "mid_term": "中线趋势判断",
    "short_term": "短线趋势判断"
  }},
  "key_levels": {{
    "strong_resistance": ["价位1", "价位2"],
    "strong_support": ["价位1", "价位2"]
  }},
  "volume_oi_linkage": "重点分析成交量、持仓量（oi）及持仓变化（oi_chg）三者之间的联动关系和含义（例如：放量下跌+OI增加=空头主动增仓）",
  "key_events": [
    {{
      "date": "YYYY-MM-DD",
      "event": "事件简述（如：放量大阴线 + OI大幅增加）",
      "interpretation": "对该事件的解读和意义"
    }}
  ],
  "force_comparison": "当前多空力量对比总结（谁更占优、强度如何）",
  "trading_bias": "当前最优交易倾向（做多 / 做空 / 观望）及核心理由",
  "main_contradiction": "当前市场的主要矛盾、风险点或不确定性",
  "playbook_references": ["具体引用的 Playbook 规则名称，例如：量仓核心逻辑（2.1）、示例2：关键压力位量仓观察"]
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
            "volume_oi_linkage": "解析失败",
            "key_events": [],
            "force_comparison": "解析失败",
            "trading_bias": "解析失败",
            "main_contradiction": "解析失败",
            "playbook_references": []
        }

    state["observations"].append(obs_data)
    return state
