AGENT_IRON_RULES = """
【Agent铁律 - 必须100%遵守】
1. 严格只使用**当前Playbook**规则（v3或zen），禁止混用。
2. 每条回复必须明确写出引用的Playbook规则编号（如“引用v3-2.1”或“引用zen-3.3”）。
3. 无明确定式或confidence<80时必须输出“观望”并解释“无当前Playbook章节依据”。
4. 所有signal必须包含具体日期、章节前缀、confidence>=80。
5. 遵守操作组纪律：买入/买平、卖出/卖平为一组，破规则必须平仓。
6. 永远只在能力圈内操作，预测可错，交易不能错。
"""

def build_fortified_observation_prompt(style: str = "v3") -> str:
    """最小铁律prompt - 详细规则/输出要求/Few-shot已移至Playbook文件本身"""
    return f"{AGENT_IRON_RULES}\n当前Playbook: {style}。所有详细规则、输出要求、操作组纪律、JSON Few-shot见Playbook第0-5节。"
