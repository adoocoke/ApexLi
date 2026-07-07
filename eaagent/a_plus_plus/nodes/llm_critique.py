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

    # 构建 Prompt - 让 LLM 自主决定轮次（不再强制多轮）。强化避免重复相同视觉图像
    prompt = f"""你是一个严格且专业的交易策略风险审查员。根据当前信息**自主决定是否需要继续多轮分析**（不再强制固定轮次）。如果数据已充分（置信度>85%、信号一致、无新风险/矛盾、工具数据足够、**K线图像已充分分析无新形态**），直接 should_continue=false 结束；否则继续调用工具获取更多持仓/新闻/相关品种数据（**不要重复调用相同visual_analyzer或生成相同图像**）。

当前轮次信息：
- 轮次: {state['iteration']} / MAX=5
- 置信度: {state.get('confidence', 0):.0%}
- 本轮发现的问题: {issues}
- 本轮交易信号: {signals[-1] if signals else '无'}
- 本轮结构化观察摘要: {observations[-1] if observations else '无'}
- 图像缓存: {observations[-1].get('is_cached_image', False) if observations else False} (True=复用相同12mo图像)

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
4. 是否有新的重要量仓特征或工具数据 (holding/related/news) 出现？

请严格按照以下 JSON 格式返回（不要有任何额外文字）：
{{
  "should_continue": true/false,
  "reason": "是否继续下一轮的理由（明确说明数据是否充分）",
  "comparison_summary": "前后轮对比的核心结论（例如：空头力量增强、信号方向一致、风险上升等）",
  "risk_change": "上升 / 下降 / 不变",
  "score": 85,  // Phase 3: 0-100 Critique 评分 (用于 Dashboard 柱状图和报告)
  "key_rules": ["2.1 量仓分析", "3.1 背驰判断"]  // 主要规则 (真实数据)
}}"""
    else:
        prompt += """
请判断当前分析是否充分（置信度、信号一致性、工具数据），是否建议继续下一轮。
请严格按照以下 JSON 格式返回：
{{
  "should_continue": true/false,
  "reason": "判断理由（明确说明数据是否充分或需要更多工具）",
  "comparison_summary": "当前分析的核心结论",
  "risk_change": "上升 / 下降 / 不变",
  "score": 92,  // Phase 3: 0-100 Critique 评分 (用于 Dashboard 柱状图和报告)
  "key_rules": ["2.1 量仓分析", "4.2 定式确认"]  // 主要规则 (真实数据)
}}"""

    system_prompt = state["messages"][0]["content"] if state.get("messages") else ""
    response = call_llm(prompt, system_prompt)  # llm.py now robust (returns JSON string on None/empty/error)

    state["critique_result"] = {
        "raw_response": response,
        "has_previous_round": prev_observation is not None
    }

    # Phase 3: 真实critique_score + key_rules (robust re.search + default JSON)
    try:
        import json, re
        if not isinstance(response, str) or not response.strip():
            response = '{"should_continue": false, "reason": "Empty response from call_llm", "score": 85, "key_rules": ["default"]}'
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(response) if isinstance(response, str) else {}
        score = int(data.get("score", 85))
        rules = data.get("key_rules", ["Playbook规则匹配"])
        should_continue = data.get("should_continue", False)
    except Exception as e:
        print(f"[Critique] JSON parse error: {e}, raw preview: {str(response)[:150] if response else 'None'}")
        score = 85
        rules = ["default fallback"]
        should_continue = False

    if "critique_scores" not in state:
        state["critique_scores"] = []
    state["critique_scores"].append(score)
    state["critique_result"].update({
        "score": score,
        "key_rules": rules,
        "should_continue": should_continue
    })

    color_print(f"  → Critique score: {score} | Continue: {should_continue} | Rules: {rules[:2]}", Colors.OKBLUE if score > 80 else Colors.WARNING)
    return state
