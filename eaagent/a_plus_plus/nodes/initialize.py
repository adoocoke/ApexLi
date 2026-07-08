import os
from datetime import datetime
from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.playbooks.manager import manager

def initialize_state(state: TAState) -> TAState:
    color_print("\n" + "="*70, Colors.BOLD)
    color_print(f"[初始化] 开始分析 {state['current_symbol']}", Colors.BOLD)
    color_print(f"  - 数据来源: {state['data_source'].upper()}", Colors.OKCYAN)

    # 强制使用 Web 选择的 Playbook
    pb = state.get("current_playbook", "v3")
    color_print(f"  - Playbook: {pb} ← 来自Web选择", Colors.OKGREEN)

    # 只加载一次
    content, name = manager.load(pb)
    state["current_playbook"] = name
    state["playbook_used"] = True
    state["playbook_id"] = manager.get_id(name)

    # Strategy 切换 (支持 env var + Web)
    strategy_name = os.getenv("PLAYBOOK_STRATEGY", "full").lower()
    if strategy_name == "core":
        from eaagent.a_plus_plus.strategies.playbook_strategies import CoreRulesStrategy
        strategy = CoreRulesStrategy()
        color_print(f"[Playbook] 使用 CoreRulesStrategy (精简规则) → {name}", Colors.OKGREEN)
    elif strategy_name == "idonly":
        from eaagent.a_plus_plus.strategies.playbook_strategies import IdOnlyStrategy
        strategy = IdOnlyStrategy()
        color_print(f"[Playbook] 使用 IdOnlyStrategy (仅ID) → {name}", Colors.OKGREEN)
    else:
        from eaagent.a_plus_plus.strategies.playbook_strategies import FullPlaybookStrategy
        strategy = FullPlaybookStrategy()
        color_print(f"[Playbook] 使用完整策略 (Full) → {name}", Colors.OKGREEN)

    system_prompt = strategy.get_system_prompt(content, state["playbook_id"])
    state["messages"].append({"role": "system", "content": system_prompt})

    color_print(f"  - 最大分析轮次: {state['max_rounds']}", Colors.OKCYAN)
    color_print("="*70, Colors.BOLD)
    return state