from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.a_plus_plus.utils.llm import call_llm


def llm_critique(state: TAState) -> TAState:
    color_print(f"\n[第 {state['iteration']} 轮] LLM Critique（Grok 审查）", Colors.HEADER)

    observations = state.get("observations", [])
    signals = state.get("signals", [])
    issues = state.get("issues", [])

    # 获取上一轮信息（如果存在）
    prev_observation = observations[-2] if len(observations) >= 2 else None
    prev_signal = signals[-2] if len(signals) >= 2 else None
    prev_issues = state.get("previous_issues", [])

    # 构建 Prompt
    prompt = f"""你是一个严格且专业的交易策略风险审查员。

当前轮次信息：
- 轮次: {state['iteration']}
- 置信度: {state.get('confidence', 0):.0%}
- 本轮发现的问题: {issues}
- 本轮交易信号: {signals[-1] if signals else '无'}
- 本轮结构化观察摘要: {observations[-1] if observations else '无'}

"""

    if prev_observation:
        prompt += f"""上一轮关键信息：
- 上一轮交易信号: {prev_signal}
- 上一轮发现的问题: {prev_issues}
- 上一轮观察摘要: {prev_observation}

请对比本轮与上一轮，重点分析：
1. 交易方向（多/空/观望）是否发生变化？
2. 空头/多头力量是否增强或减弱？
3. 风险是上升、下降还是保持不变？
4. 是否有新的重要量仓特征出现？

请严格按照以下 JSON 格式返回（不要有任何额外文字）：
{{
  "should_continue": true/false,
  "reason": "是否继续下一轮的理由（简洁明确）",
  "comparison_summary": "前后轮对比的核心结论（例如：空头力量增强、信号方向一致、风险上升等）",
  "risk_change": "上升 / 下降 / 不变"
}}"""
    else:
        prompt += """
请判断当前分析是否充分，是否建议继续下一轮，并给出理由。
请严格按照以下 JSON 格式返回：
{{
  "should_continue": true/false,
  "reason": "判断理由",
  "comparison_summary": "当前分析的核心结论",
  "risk_change": "上升 / 下降 / 不变"
}}"""

    system_prompt = state["messages"][0]["content"] if state.get("messages") else ""
    response = call_llm(prompt, system_prompt)

    state["critique_result"] = {
        "raw_response": response,
        "has_previous_round": prev_observation is not None
    }

    return state
