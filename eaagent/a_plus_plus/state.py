from typing import TypedDict, List, Optional, Dict, Any
from langchain_core.messages import BaseMessage

class APlusPlusState(TypedDict):
    """扩展的状态定义，继承 eaagent 基础状态 + A++ 特有字段"""

    # === 基础消息历史（LangGraph 标准） ===
    messages: List[BaseMessage]

    # === Playbook 相关 ===
    playbook_rules: Optional[Dict[str, Any]]          # 加载后的结构化 Playbook
    rag_context: Optional[str]                        # RAG 检索到的相关规则片段

    # === 当前交易状态 ===
    current_position: Optional[Dict[str, Any]]        # 当前持仓信息
    current_symbol: Optional[str]                     # 当前分析的品种
    current_timeframe: Optional[str]                  # 当前分析的时间框架

    # === 反馈与成长（AIFED） ===
    feedback_log: List[Dict[str, Any]]                # 人类反馈历史
    reflection_notes: Optional[str]                   # Reflection Node 的自我批评

    # === 执行控制 ===
    next_action: Optional[str]                        # 下一个建议动作（用于 human-in-the-loop）
    interrupt_reason: Optional[str]                   # 中断原因（如果需要人类确认）


def create_initial_state() -> APlusPlusState:
    """创建初始状态"""
    return APlusPlusState(
        messages=[],
        playbook_rules=None,
        rag_context=None,
        current_position=None,
        current_symbol=None,
        current_timeframe=None,
        feedback_log=[],
        reflection_notes=None,
        next_action=None,
        interrupt_reason=None,
    )
