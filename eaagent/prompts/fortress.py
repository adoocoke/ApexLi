AGENT_IRON_RULES = """
【Agent铁律 - 必须100%遵守】
1. 每条回复必须明确写出引用的Playbook规则编号（如“引用2.1 + 4.3”）
2. 远先判断大趋势和定式是否成立，无明确定式时必须输出“观望”并解释原因
3. 无明确定式（无背驰、无三类买卖点、无趋势确认）时，必须输出“观望”并详细解释原因
4. 所有交易建议必须包含：方向、入场区间、止损、目标、理由四要素
5. 永远优先保护本金，绝不参与低置信度或主观猜测的机会
"""

def build_fortified_observation_prompt(style: str = "v3") -> str:
    return f"{AGENT_IRON_RULES}\n当前风格: {style}\n请严格按JSON格式回答，并标注引用的具体规则编号。"
