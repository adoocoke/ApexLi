"""
eaagent/a_plus_plus/graph.py
高质量自动分析版 + 混合模式 + 开仓理由数量控制提前结束
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import os
import re

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .data_provider import get_market_data
from .playbook_loader import load_playbook, build_playbook_prompt, get_relevant_playbook_rules
from .config import MAX_ROUNDS


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
    critique_result: Optional[dict]
    reason_count: int          # 新增：当前开仓理由数量


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
        max_rounds=MAX_ROUNDS,
        critique_result=None,
        reason_count=0,
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

    llm_response = "根据当前量仓和多时间框架分析，建议做多，止损设在 4080。"

    # 简单统计理由数量（按句号或分号拆分）
    reason_points = len(re.split(r'[。；;]', llm_response))
    state["reason_count"] = reason_points

    print(f"[LLM Response] {llm_response}")
    print(f"  → 本轮开仓理由数量: {reason_points}\n")

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
        print(f"  → 确定性检查发现的问题: {issues}")

    return state


def llm_critique(state: TAState) -> TAState:
    print(f"\n[第 {state['iteration']} 轮] LLM Critique（大模型深度分析）")

    critique_prompt = f"""你是一个严格的风险与质量审查员。

当前分析状态：
- 品种：{state['current_symbol']}
- 当前轮次：{state['iteration']}
- 置信度：{state['confidence']}
- 开仓理由数量：{state.get('reason_count', 0)}
- 已发现问题：{state['issues']}

请结合 Playbook 规则判断：
1. 当前开仓理由是否合理（数量是否合适）？
2. 是否建议继续下一轮分析？

请用 JSON 返回：
{{
  "should_continue": true/false,
  "reason": "简短理由"
}}
"""

    print("\n" + "-"*50)
    print("[LLM Critique Prompt] 发送给大模型的审查 Prompt：")
    print(critique_prompt)
    print("-"*50)

    # 模拟 LLM 返回
    llm_critique_response = {
        "should_continue": True,
        "reason": "当前分析较为充分，可以考虑结束或继续观察"
    }

    print(f"\n[LLM Critique Response] {llm_critique_response}\n")

    state["critique_result"] = llm_critique_response
    return state


def should_continue_after_critique(state: TAState) -> Literal["continue", "finalize"]:
    reason_count = state.get("reason_count", 0)
    critique = state.get("critique_result", {})

    # 核心判断：开仓理由数量 < 2 或 > 5 时，提前结束
    if reason_count < 2 or reason_count > 5:
        print(f"  → 开仓理由数量异常（{reason_count}个），建议提前结束分析\n")
        return "finalize"

    if critique.get("should_continue") and state["iteration"] < state["max_rounds"]:
        print(f"  → LLM 建议继续，进入第 {state['iteration'] + 1} 轮...\n")
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
    workflow.add_node("llm_critique", llm_critique)
    workflow.add_node("final_output", final_output)
    workflow.add_node("persist", persist)

    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "data_ingestion")
    workflow.add_edge("data_ingestion", "observation")
    workflow.add_edge("observation", "signal_gen")
    workflow.add_edge("signal_gen", "quality_sensor")
    workflow.add_edge("quality_sensor", "llm_critique")

    workflow.add_conditional_edges(
        "llm_critique",
        should_continue_after_critique,
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
    print("=== EA Agent - 默认5轮 + 开仓理由数量控制 ===\n")
    app = build_graph()
    state = create_initial_state("RB2605")
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)
