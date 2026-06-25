"""
eaagent/a_plus_plus/graph.py
重构后版本 - Harness 核心逻辑
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import os
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .data_provider import get_market_data, get_historical_data
from .playbook_loader import load_playbook, build_playbook_prompt, get_relevant_playbook_rules, get_playbook_id, PLAYBOOK_CONTENT
from .config import MAX_ROUNDS
from .types import TAState

# ==================== 工具模块 ====================
from .utils.llm import call_llm
from .utils.console import color_print, Colors

# ==================== 节点模块 ====================
from .nodes import persist, data_ingestion
from .nodes.observation import structured_observation
from eaagent.data_providers.factory import get_data_provider


def create_initial_state(symbol: str = "RB2605.SHF") -> TAState:
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
        playbook_id="",
        playbook_content_sent=False,
    )


def initialize_state(state: TAState) -> TAState:
    color_print("\n" + "="*70, Colors.BOLD)
    color_print(f"[初始化] 开始分析 {state['current_symbol']}", Colors.BOLD)
    color_print(f"  - 数据来源: {state['data_source'].upper()}", Colors.OKCYAN)

    if load_playbook():
        state["playbook_used"] = True
        from eaagent.a_plus_plus.strategies.playbook_strategies import (
            FullPlaybookStrategy,
            CoreRulesStrategy,
            IdOnlyStrategy
        )

        playbook_id = get_playbook_id(PLAYBOOK_CONTENT)
        state["playbook_id"] = playbook_id

        strategy_mode = os.getenv("PLAYBOOK_STRATEGY", "full").lower()

        if not state.get("playbook_content_sent", False):
            if strategy_mode == "core":
                strategy = CoreRulesStrategy()
                color_print(f"[Playbook] 使用核心规则策略，ID: {playbook_id}", Colors.OKGREEN)
            else:
                strategy = FullPlaybookStrategy()
                color_print(f"[Playbook] 使用完整策略，ID: {playbook_id}", Colors.OKGREEN)

            state["playbook_content_sent"] = True
        else:
            strategy = IdOnlyStrategy()
            color_print(f"[Playbook] 使用 ID 策略，ID: {playbook_id}", Colors.OKCYAN)

        system_prompt = strategy.get_system_prompt(PLAYBOOK_CONTENT, playbook_id)
        state["messages"].append({"role": "system", "content": system_prompt})
    else:
        state["playbook_used"] = False

    color_print(f"  - 最大分析轮次: {state['max_rounds']}", Colors.OKCYAN)
    color_print("="*70, Colors.BOLD)
    return state


def signal_generation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 生成交易信号（Grok 分析）", Colors.OKGREEN)

    obs = state["observations"][-1] if state["observations"] else {}
    relevant_rules = get_relevant_playbook_rules("量仓 止损")

    prompt = f"""基于以下观察内容，请给出**结构化交易建议**，并严格按照 JSON 格式返回：

{obs}
参考 Playbook 规则: {relevant_rules}

请返回以下 JSON 格式（不要有额外文字）：
{{
  "direction": "多头 / 空头 / 观望",
  "entry_zone": "入场区间描述",
  "stop_loss": "止损描述",
  "target": "目标 / 减仓区间",
  "reason": "详细理由（必须引用 Playbook 相关逻辑）"
}}"""

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    try:
        signal_data = json.loads(response)
    except json.JSONDecodeError:
        signal_data = {
            "direction": "观望",
            "entry_zone": "解析失败",
            "stop_loss": "解析失败",
            "target": "解析失败",
            "reason": response
        }

    state["signals"].append(signal_data)
    state["confidence"] = round(0.65 + (state["iteration"] * 0.08), 2)
    return state


def quality_sensor(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 质量检查 (Sensors)", Colors.WARNING)

    issues = []
    latest_signal = state["signals"][-1] if state["signals"] else {}
    reason = latest_signal.get("reason", "")
    has_risk_control = any(kw in reason for kw in ["止损", "风险", "仓位", "轻仓"])

    if len(state["observations"]) < 2:
        issues.append("观察数据不足（当前仅1条结构化观察）")

    if state["confidence"] < 0.75 and not has_risk_control:
        issues.append(f"置信度偏低（当前 {state['confidence']:.0%}），建议继续分析")

    state["issues"] = issues
    state["risk_assessment"] = {"issues_count": len(issues), "issues": issues}
    state["analysis_rounds"] = state["iteration"]

    if issues:
        color_print(f"  → 发现的问题: {issues}", Colors.FAIL)
    else:
        color_print("  → 未发现明显问题", Colors.OKGREEN)

    return state


def llm_critique(state: TAState) -> TAState:
    color_print(f"\n[第 {state['iteration']} 轮] LLM Critique（Grok 审查）", Colors.HEADER)

    prompt = f"""你是一个严格的风险审查员。

当前状态：
- 轮次: {state['iteration']}
- 置信度: {state['confidence']}
- 已发现问题: {state['issues']}
- 最新信号: {state['signals'][-1] if state['signals'] else '无'}

请判断是否建议继续下一轮分析，并给出理由。

请用 JSON 返回：{{"should_continue": true/false, "reason": "..."}}"""

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    state["critique_result"] = {"raw_response": response}
    return state


def should_continue_after_critique(state: TAState) -> Literal["continue", "finalize"]:
    if state["iteration"] >= state["max_rounds"]:
        return "finalize"

    raw = state.get("critique_result", {}).get("raw_response", "")
    if "false" in raw.lower():
        return "finalize"

    return "continue"


def final_output(state: TAState) -> TAState:
    color_print("\n" + "="*70, Colors.BOLD)
    color_print(f"【{state['current_symbol']} 技术分析报告】（共 {state['analysis_rounds']} 轮）", Colors.BOLD)
    color_print("="*70, Colors.BOLD)

    color_print(f"数据来源: {state['data_source'].upper()}", Colors.OKCYAN)
    color_print(f"Playbook 使用: {'是' if state['playbook_used'] else '否'}", Colors.OKCYAN)
    color_print(f"实际分析轮次: {state['analysis_rounds']}", Colors.OKCYAN)

    if state["signals"]:
        last_signal = state["signals"][-1]
        color_print("\n最终交易信号:", Colors.OKGREEN)
        print(json.dumps(last_signal, ensure_ascii=False, indent=2))

    if state["issues"]:
        color_print("\n⚠️  最终问题:", Colors.FAIL)
        for issue in state["issues"]:
            print(f"  • {issue}")
    else:
        color_print("\n✅ 分析完成", Colors.OKGREEN)

    color_print("="*70, Colors.BOLD)
    return state


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
        {"continue": "data_ingestion", "finalize": "final_output"}
    )

    workflow.add_edge("final_output", "persist")
    workflow.add_edge("persist", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


if __name__ == "__main__":
    color_print("=== EA Agent - Harness 重构版 ===", Colors.BOLD)
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)
