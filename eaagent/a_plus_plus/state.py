from typing import TypedDict, List, Optional, Dict, Any

# Use total=False for compatibility (fix TypedDict extra_items error from langchain_protocol/langgraph)

# 避免langchain_core/langgraph_sdk版本冲突 (extra_items / TypedDict)
# 使用dict作为BaseMessage占位 (streamlit环境下避免导入langchain_protocol)
BaseMessage = dict
HAS_LANGCHAIN = False


class APlusPlusState(TypedDict, total=False):
    """扩展的状态定义，继承 eaagent 基础状态 + A++ 特有字段"""

    # === 基础消息历史（LangGraph 标准） ===
    messages: List[BaseMessage]

    # === Playbook 相关 ===
    playbook_rules: Optional[Dict[str, Any]]
    rag_context: Optional[str]

    # === 当前交易状态 ===
    current_position: Optional[Dict[str, Any]]
    current_symbol: Optional[str]
    current_timeframe: Optional[str]

    # === 反馈与成长（AIFED） ===
    feedback_log: List[Dict[str, Any]]
    reflection_notes: Optional[str]

    # === 执行控制 ===
    next_action: Optional[str]
    interrupt_reason: Optional[str]


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
