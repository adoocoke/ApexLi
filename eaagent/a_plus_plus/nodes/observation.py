from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
import json
import pandas as pd
from typing import List, Dict, Any


def _prepare_daily_data(daily_data: List[Dict[str, Any]], max_rows: int = 40) -> str:
    """将日线数据处理成简洁的文本，供 LLM 使用"""
    if not daily_data:
        return "历史日线数据为空"

    df = pd.DataFrame(daily_data)
    keep_cols = ["trade_date", "open", "high", "low", "close", "vol", "oi"]
    df = df[[c for c in keep_cols if c in df.columns]]
    df = df.tail(max_rows)

    return df.to_csv(index=False)


def structured_observation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 结构化市场观察", Colors.OKCYAN)

    market_data = state.get("market_data", {})
    daily_data = market_data.get("daily_df", [])

    if not daily_data:
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

    data_str = _prepare_daily_data(daily_data, max_rows=40)

    prompt = f"""以下是 {state['current_symbol']} 最近的日线数据（CSV 格式，包含最近最多40根K线）：

{data_str}

请基于以上数据进行**专业、深入**的技术分析，并严格按照以下 JSON 格式返回结果（不要有任何额外文字）：

{{
  "phase": "当前所处阶段，例如：下跌中继 / 反弹确认 / 筑底阶段 / 趋势反转初期 / 高位震荡 等",
  "trend": {{
    "mid_term": "中线趋势判断",
    "short_term": "短线趋势判断"
  }},
  "key_levels": {{
    "strong_resistance": ["具体价位1", "具体价位2"],
    "strong_support": ["具体价位1", "具体价位2"]
  }},
  "volume_analysis": "对成交量的分析，例如：放量杀跌 / 缩量反弹 / 量价背离 / 恐慌性放量 等",
  "oi_analysis": "对持仓量（OI）的分析，例如：多头增仓 / 空头减仓 / OI高位滞涨 / OI与价格背离 等",
  "pattern": "当前K线形态或结构，例如：下跌通道 / 平台整理 / V型反转 / 假突破 / 连续放量阴线 等",
  "conclusion": "综合结论，例如：短期偏空，建议反弹做空 / 筑底阶段，观望为主 / 趋势反转信号出现 等",
  "risk_note": "当前主要风险点",
  "playbook_references": ["具体引用的Playbook规则或示例，例如：量仓核心逻辑、关键压力位量仓观察、示例3波段操作等"]
}}"""

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""

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
