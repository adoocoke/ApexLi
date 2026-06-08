"""
A++ 模块（A Plus Plus）

该模块在 eaagent 基础上扩展了以下能力：
- Playbook 注入（trading_playbook_v3.md）
- 扩展状态管理（APlusPlusState）
- LangGraph 工作流支持
- 人类反馈闭环（AIFED）

使用示例：
    from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent
"""

from .eaagent_wrapper import APlusPlusReActAgent
from .state import APlusPlusState, create_initial_state
from .prompt_builder import PlaybookPromptBuilder

__all__ = [
    "APlusPlusReActAgent",
    "APlusPlusState",
    "create_initial_state",
    "PlaybookPromptBuilder",
]
