from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.data_provider import get_historical_data
from eaagent.a_plus_plus.utils.console import color_print, Colors
import json


def structured_observation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 结构化市场观察", Colors.OKCYAN)

    df = get_historical_data(
        symbol=state['current_symbol'],
        data_source=state['data_source']
    )

    if df.empty:
        obs_data = {
            "trend": {"mid_term": "数据缺失", "short_term": "数据缺失"},
            "key_levels": {"strong_resistance": [], "strong_support": []},
            "volume_analysis": "数据缺失",
            "pattern": "数据缺失",
            "conclusion": "历史数据为空，无法进行有效技术分析。",
            "risk_note": "数据不足",
            "playbook_references": []
        }
        state["observations"].append(obs_data)
        return state

    data_str = df.to_csv(index=False)

    prompt = f"""以下是 {state['current_symbol']} 的完整历史日线数据（CSV 格式）：

{data_str}

请基于以上全部历史数据进行专业的技术分析，并**严格按照以下 JSON 格式**返回结果（不要有任何额外文字说明）：

{{
  "trend": {{
    "mid_term": "明显下跌 / 反弹修复 / 震荡筑底 / 趋势反转 等",
    "short_term": "弱势反弹 / 加速上涨 / 高位震荡 / 假突破 等"
  }},
  "key_levels": {{
    "strong_resistance": ["价位1", "价位2"],
    "strong_support": ["价位1", "价位2"]
  }},
  "volume_analysis": "缩量反弹 / 放量突破 / 量价背离 / 恐慌性放量杀跌 等",
  "pattern": "V型反转 / 平台整理 / 矩形箱体 / 假突破 / 单日反转 等",
  "conclusion": "短期偏多但需突破确认 / 反弹做空为主 / 观望等待量能确认 等",
  "risk_note": "量能不足 / OI高位 / 关键压力位未有效突破 / 二次探底风险 等",
  "playbook_references": ["量仓核心逻辑", "关键压力位量仓观察"]
}}"""

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    from eaagent.a_plus_plus.utils.llm import call_llm
    response = call_llm(prompt, system_prompt)

    try:
        obs_data = json.loads(response)
    except json.JSONDecodeError:
        obs_data = {
            "trend": {"mid_term": "解析失败", "short_term": "解析失败"},
            "key_levels": {"strong_resistance": [], "strong_support": []},
            "volume_analysis": "解析失败",
            "pattern": "解析失败",
            "conclusion": response[:500],
            "risk_note": "LLM 返回格式异常",
            "playbook_references": []
        }

    state["observations"].append(obs_data)
    return state
