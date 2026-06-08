from typing import TypedDict, List, Optional, Dict, Any

# 尝试导入 langchain_core，如果没有安装则使用占位类型
try:
    from langchain_core.messages import BaseMessage
    HAS_LANGCHAIN = True
except ImportError:
    BaseMessage = dict  # 占位类型
    HAS_LANGCHAIN = False


class APlusPlusState(TypedDict):
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
