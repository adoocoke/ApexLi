# Prompt Fortress - 强制规则中心
AGENT_IRON_RULES = """
【Agent铁律 - 必须严格遵守】
1. 必须在回复中明确写出引用的Playbook规则编号（如“引用2.1 + 4.3”）
2. 永远先判断大趋势和定式是否成立，无明确定式时必须输出“观望”并解释原因
3. 所有交易建议必须包含入场、止损、目标、理由四要素
4. 永远优先保护本金，绝不追高杀跌或参与低置信度机会
"""

def build_fortified_prompt(playbook_content: str, style: str = "v3") -> str:
    return f"{AGENT_IRON_RULES}\n当前Playbook风格: {style}\n\n{playbook_content[:3500]}"
