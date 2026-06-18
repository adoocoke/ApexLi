"""
eaagent/a_plus_plus/graph.py
只负责 LangGraph 流程编排（保持干净）
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import os

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .data_provider import get_market_data
from .playbook_loader import load_playbook, build_playbook_prompt, get_relevant_playbook_rules


class TAState(TypedDict):
    current_symbol: str
    messages: List[dict]
    thread_id: str
    timeframes: List[str]
    market_data: Dict[str, Any]
    observations: List[dict]
    patterns: List[dict]
    signals: List[dict]
    risk_assessment: Dict[str, Any]
    confidence: float
    artifacts: List[str]
    issues: List[str]
    verification_result: Optional[dict]
    human_feedback: Optional[str]
    iteration: int
    is_done: bool
    created_at: datetime
    last_updated: datetime
    data_source: str
    playbook_used: bool
    analysis_rounds: int
    max_rounds: int


def create_initial_state(symbol: str = "RB2605") -> TAState:
    now = datetime.now()
    use_mock = os.getenv("USE_MOCK_OBSERVATION", "true").lower() == "true"

    return TAState(
        current_symbol=symbol,
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
        max_rounds=3,
    )


# ==================== 节点 ====================
def initialize_state(state: TAState) -> TAState:
    print("\n" + "="*70)
    print(f"[初始化] 开始分析 {state['current_symbol']}")
    print(f"  - 数据来源: {state['data_source'].upper()}")

    if load_playbook():
        state["playbook_used"] = True
        state["messages"].append({"role": "system", "content": build_playbook_prompt()})
    else:
        state["playbook_used"] = False
        state["messages"].append({
            "role": "system",
            "content": "你是一个专业的期货技术分析师，请严格遵守交易纪律进行分析。"
        })

    print(f"  - 最大分析轮次: {state['max_rounds']}")
    print("="*70)
    return state


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    state["market_data"] = get_market_data(
        state["data_source"], state["current_symbol"], state["timeframes"]
    )
    return state


def structured_observation(state: TAState) -> TAState:
    print(f"[第 {state['iteration']} 轮] 结构化市场观察")
    relevant_rules = get_relevant_playbook_rules("量仓 支撑 阻力")
    if relevant_rules:
        print(f"  → 参考 Playbook 规则: {relevant_rules}")

    state["observations"].append({
        "volume_position_change": "放量增仓",
        "key_levels": [4080, 4150],
        "atr_status": "正常区间"
    })
    return state


def signal_generation(state: TAState) -> TAState:
    print(f"[第 {state['iteration']} 轮] 生成交易信号")
    relevant_rules = get_relevant_playbook_rules("止损 量仓 时间框架")
    if relevant_rules:
        print(f"  → 参考 Playbook 规则: {relevant_rules}")

    # 这里可以后续替换为真实 LLM 调用
    llm_response = "根据当前量仓和多时间框架分析，建议做多，止损设在 4080。"
    print(f"[LLM Response] {llm_response}\n")

    state["signals"].append({
        "direction": "多头",
        "entry": 4125,
        "stop_loss": 4080,
        "timeframe": "30m",
        "reason": llm_response
    })
    state["confidence"] = round(0.65 + (state["iteration"] * 0.08), 2)
    return state


def quality_sensor(state: TAState) -> TAState:
    print(f"[第 {state['iteration']} 轮] 质量检查 (Sensors)")
    relevant_rules = get_relevant_playbook_rules("风险 止损")
    if relevant_rules:
        print(f"  → 参考 Playbook 规则: {relevant_rules}")

    issues = []
    if len(state["observations"]) < 2:
        issues.append("观察数据不足（当前仅1条结构化观察）")
    if state["confidence"] < 0.75:
        issues.append(f"置信度偏低（当前 {state['confidence']:.0%}），建议继续分析")

    state["issues"] = issues
    state["risk_assessment"] = {"issues_count": len(issues), "issues": issues}
    state["analysis_rounds"] = state["iteration"]

    if issues:
        print(f"  → 发现的问题: {issues}")

    return state


def should_continue(state: TAState) -> Literal["continue", "finalize"]:
    if len(state["issues"]) > 0 and state["iteration"] < state["max_rounds"]:
        print(f"  → 发现问题，进入第 {state['iteration'] + 1} 轮...\n")
        return "continue"
    return "finalize"


def final_output(state: TAState) -> TAState:
    print("\n" + "="*70)
    print(f"【{state['current_symbol']} 技术分析报告】（共 {state['analysis_rounds']} 轮）")
    print("="*70)
    print(f"数据来源: {state['data_source'].upper()}")
    print(f"Playbook 使用: {'是' if state['playbook_used'] else '否'}")
    print(f"实际分析轮次: {state['analysis_rounds']}")
    print(f"最终综合置信度: {state['confidence']:.0%}")

    if state["signals"]:
        print("\n最终交易信号:")
        for sig in state["signals"][-1:]:
            print(f"  • {sig['direction']} | 入场 {sig['entry']} | 止损 {sig.get('stop_loss')}")
            print(f"    LLM 理由: {sig.get('reason', '')}")

    if state["issues"]:
        print("\n⚠️  最终仍存在的问题:")
        for issue in state["issues"]:
            print(f"  • {issue}")
    else:
        print("\n✅ 分析完成，未发现明显问题")
    print("="*70)
    return state


def persist(state: TAState) -> TAState:
    print("[结束] 保存分析结果...")
    state["artifacts"].append(f"report_{state['thread_id']}.md")
    state["is_done"] = True
    return state


# ==================== 构建 Graph ====================
def build_graph():
    workflow = StateGraph(TAState)

    workflow.add_node("initialize", initialize_state)
    workflow.add_node("data_ingestion", data_ingestion)
    workflow.add_node("observation", structured_observation)
    workflow.add_node("signal_gen", signal_generation)
    workflow.add_node("quality_sensor", quality_sensor)
    workflow.add_node("final_output", final_output)
    workflow.add_node("persist", persist)

    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "data_ingestion")
    workflow.add_edge("data_ingestion", "observation")
    workflow.add_edge("observation", "signal_gen")
    workflow.add_edge("signal_gen", "quality_sensor")

    workflow.add_conditional_edges(
        "quality_sensor",
        should_continue,
        {
            "continue": "data_ingestion",
            "finalize": "final_output"
        }
    )

    workflow.add_edge("final_output", "persist")
    workflow.add_edge("persist", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


if __name__ == "__main__":
    print("=== EA Agent - 重构版 ===\n")
    app = build_graph()
    state = create_initial_state("RB2605")
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)
