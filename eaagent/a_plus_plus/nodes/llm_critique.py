from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.a_plus_plus.utils.llm import call_llm


def llm_critique(state: TAState) -> TAState:
    color_print(f"\n[第 {state['iteration']} 轮] LLM Critique（Grok 审查）", Colors.HEADER)

    prompt = f"""你是一个严格的风险审查员。
当前状态：
- 轮次: {state['iteration']}
- 置信度: {state['confidence']}
- 已发现问题: {state['issues']}
- 最新信号: {state['signals'][-1] if state['signals'] else '无'}

请判断是否建议继续下一轮分析，并给出理由。
请用 JSON 返回：{{"should_continue": true/false, "reason": "..."}}"""

    system_prompt = state["messages"][0]["content"] if state.get("messages") else ""
    response = call_llm(prompt, system_prompt)

    state["critique_result"] = {"raw_response": response}
    return state
