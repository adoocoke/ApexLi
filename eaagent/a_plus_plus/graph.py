"""
eaagent/a_plus_plus/graph.py
重构后版本 - Harness 核心逻辑
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Literal

# Lazy imports to avoid langchain_protocol / langgraph_sdk TypedDict 'extra_items' conflict in streamlit
# (pydantic_core error)
def _lazy_import_graph():
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import StateGraph, END
    from .types import TAState
    from eaagent.playbooks.manager import manager
    from .config import MAX_ROUNDS
    from .nodes import persist, data_ingestion
    from .nodes.data_gathering import data_gathering
    from .nodes.final_output import final_output
    from .nodes.initialize import initialize_state
    from .nodes.llm_critique import llm_critique
    from .nodes.observation import structured_observation
    from .nodes.quality_sensor import quality_sensor
    from .nodes.signal_generation import signal_generation
    from .utils.console import color_print, Colors
    from .utils.llm import call_llm
    return (MemorySaver, StateGraph, END, TAState, manager, MAX_ROUNDS, persist, data_ingestion, data_gathering, initialize_state, signal_generation,final_output,
            llm_critique, structured_observation, quality_sensor, color_print, Colors, call_llm)

# Global lazy objects
(_MemorySaver, _StateGraph, _END, TAState, manager, MAX_ROUNDS, persist, data_ingestion, data_gathering, initialize_state, signal_generation,
 final_output, llm_critique, structured_observation, quality_sensor, color_print, Colors, call_llm) = _lazy_import_graph()


def create_initial_state(symbol: str = "RB2610.SHF", playbook_name: str = "v3") -> TAState:
    now = datetime.now()
    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"
    return TAState(
        current_symbol=symbol,
        current_playbook=playbook_name,   # ← 新增这一行，关键！
        messages=[],
        thread_id=f"ta-{symbol}-{now.strftime('%Y%m%d%H%M%S')}",
        timeframes=["5m", "30m", "1d"],
        market_data={},
        observations=[],
        patterns=[],
        signals=[],
        risk_assessment={},
        confidence=0.0,
        artifacts=[],
        issues=[],
        verification_result=None,
        human_feedback=None,
        iteration=0,
        is_done=False,
        created_at=now,
        last_updated=now,
        data_source="mock" if use_mock else "tushare",
        playbook_used=False,
        analysis_rounds=0,
        max_rounds=MAX_ROUNDS,
        critique_result=None,
        critique_scores=[],  # Phase 3: Dashboard 柱状图/Mermaid + report_builder
        reason_count=0,
        playbook_id="",
        playbook_content_sent=False,
        interrupt_reason=None,  # Phase 3: human intervention hook
        feedback_log=[],
    )


def should_continue_after_critique(state: TAState) -> Literal["continue", "finalize"]:
    """Phase 3: 支持 human intervention + 真实 critique_scores 传播"""
    iteration = state.get("iteration", 0)
    max_rounds = state.get("max_rounds", 5)
    if iteration >= max_rounds:
        color_print("  → 达到最大轮次，结束分析", Colors.OKBLUE)
        return "finalize"

    # Phase 3 human intervention 检查
    if state.get("interrupt_reason") or state.get("human_feedback"):
        color_print(f"  → 人工干预触发: {state.get('interrupt_reason') or state.get('human_feedback')}", Colors.WARNING)
        return "finalize"

    critique = state.get("critique_result", {})
    raw_response = critique.get("raw_response", "")
    should_continue_from_critique = critique.get("should_continue", None)

    # 优先使用 llm_critique 已解析的 should_continue (robust JSON)
    if should_continue_from_critique is not None:
        reason = critique.get("reason", "LLM critique decision")
        color_print(f"  → LLM 决定: should_continue={should_continue_from_critique} | {reason}", Colors.OKCYAN)
        return "continue" if should_continue_from_critique else "finalize"

    # Fallback: parse raw (handles legacy NoneType)
    try:
        import json, re
        json_match = re.search(r'\{.*\}', str(raw_response), re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            should_continue = result.get("should_continue", False)
            reason = result.get("reason", "")
            color_print(f"  → LLM 决定: should_continue={should_continue} | {reason}", Colors.OKCYAN)
            return "continue" if should_continue else "finalize"
    except Exception as e:
        color_print(f"  → JSON 解析失败，默认结束: {e}", Colors.WARNING)
        pass

    # 默认行为：高置信且无问题则结束，否则继续生成更多signals
    if state.get("confidence", 0) > 0.85 and not state.get("issues"):
        return "finalize"
    return "continue"


def build_graph():
    workflow = _StateGraph(TAState)

    workflow.add_node("initialize", initialize_state)
    workflow.add_node("data_ingestion", data_ingestion)
    workflow.add_node("observation", structured_observation)
    workflow.add_node("data_gathering", data_gathering)
    workflow.add_node("signal_gen", signal_generation)
    workflow.add_node("quality_sensor", quality_sensor)
    workflow.add_node("llm_critique", llm_critique)
    workflow.add_node("final_output", final_output)
    workflow.add_node("persist", persist)

    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "data_ingestion")
    workflow.add_edge("data_ingestion", "observation")
    workflow.add_edge("observation", "data_gathering")
    workflow.add_edge("data_gathering", "signal_gen")
    workflow.add_edge("signal_gen", "quality_sensor")
    workflow.add_edge("quality_sensor", "llm_critique")

    workflow.add_conditional_edges(
        "llm_critique",
        should_continue_after_critique,
        {"continue": "data_ingestion", "finalize": "final_output"}
    )

    workflow.add_edge("final_output", "persist")
    workflow.add_edge("persist", _END)

    checkpointer = _MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


if __name__ == "__main__":
    color_print("=== EA Agent - Harness 重构版 ===", Colors.BOLD)
    app = build_graph()
    state = create_initial_state("RB2610.SHF", playbook_name="zen")  # ← 改这里测试 zen
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)