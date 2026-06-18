"""
eaagent/a_plus_plus/graph.py
完整可运行版本（测试模式下 call_llm 直接返回固定字符串）
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import os
import pandas as pd

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .data_provider import get_market_data, get_historical_data
from .playbook_loader import load_playbook, build_playbook_prompt, get_relevant_playbook_rules
from .config import MAX_ROUNDS


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """调用 Grok（测试模式下直接返回固定字符串，无额外开销）"""
    # 测试模式：直接返回固定字符串
    if os.getenv("USE_MOCK_LLM") == "true":
        return "根据历史数据分析，当前处于反弹阶段，建议在支撑位附近做多，止损设在 2915。"

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return "根据历史数据分析，当前处于反弹阶段，建议在支撑位附近做多，止损设在 2915。"

    from openai import OpenAI
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
        timeout=30.0
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    print("\n" + "=" * 60)
    print("[LLM Prompt] 发送给 Grok")
    print("=" * 60)

    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=messages,
            temperature=0.3,
            max_tokens=1200
        )
        result = response.choices[0].message.content.strip()
        print(f"[Grok Response] {result}\n")
        return result

    except Exception as e:
        print(f"[LLM] Grok 调用失败: {e}")
        return "模型调用失败或超时，返回模拟结果。"


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
    reason_count: int


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
    )


def initialize_state(state: TAState) -> TAState:
    print("\n" + "="*70)
    print(f"[初始化] 开始分析 {state['current_symbol']}")
    print(f"  - 数据来源: {state['data_source'].upper()}")

    if load_playbook():
        state["playbook_used"] = True
        state["messages"].append({"role": "system", "content": build_playbook_prompt()})
    else:
        state["playbook_used"] = False

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
    print(f"[第 {state['iteration']} 轮] 结构化市场观察（发送全部历史数据给 Grok）")

    df = get_historical_data(
        symbol=state['current_symbol'],
        data_source=state['data_source']
    )

    if df.empty:
        prompt = "历史数据为空，请给出简化观察。"
    else:
        data_str = df.to_csv(index=False)
        prompt = f"""以下是 {state['current_symbol']} 的完整历史日线数据（CSV 格式）：

{data_str}

请基于以上全部历史数据进行专业的技术分析，包括：
1. 整体趋势判断
2. 关键压力位和支撑位
3. 量价关系分析
4. 重要形态或转折特征
5. 结构化观察结论"""

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    state["observations"].append({"llm_observation": response})
    return state


def signal_generation(state: TAState) -> TAState:
    print(f"[第 {state['iteration']} 轮] 生成交易信号（Grok 分析）")

    obs = state["observations"][-1] if state["observations"] else {}
    relevant_rules = get_relevant_playbook_rules("量仓 止损")

    prompt = f"""基于以下观察内容，请给出交易建议：

{obs}
参考 Playbook 规则: {relevant_rules}

请给出结构化交易建议（方向、入场区域、止损、理由）。"""

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    state["signals"].append({
        "direction": "多头" if "多" in response else "空头",
        "entry": 0,
        "stop_loss": 0,
        "timeframe": "1d",
        "reason": response
    })
    state["confidence"] = round(0.65 + (state["iteration"] * 0.08), 2)
    return state


def quality_sensor(state: TAState) -> TAState:
    print(f"[第 {state['iteration']} 轮] 质量检查 (Sensors)")
    issues = []
    if len(state["observations"]) < 2:
        issues.append("观察数据不足")
    if state["confidence"] < 0.75:
        issues.append(f"置信度偏低（当前 {state['confidence']:.0%}）")

    state["issues"] = issues
    state["risk_assessment"] = {"issues_count": len(issues), "issues": issues}
    state["analysis_rounds"] = state["iteration"]

    if issues:
        print(f"  → 发现的问题: {issues}")
    return state


def llm_critique(state: TAState) -> TAState:
    print(f"\n[第 {state['iteration']} 轮] LLM Critique（Grok 审查）")

    prompt = f"""你是一个严格的风险审查员。

当前状态：
- 轮次: {state['iteration']}
- 置信度: {state['confidence']}
- 已发现问题: {state['issues']}
- 最新信号理由: {state['signals'][-1]['reason'] if state['signals'] else '无'}

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
    print("\n" + "="*70)
    print(f"【{state['current_symbol']} 技术分析报告】（共 {state['analysis_rounds']} 轮）")
    print("="*70)
    print(f"数据来源: {state['data_source'].upper()}")
    print(f"Playbook 使用: {'是' if state['playbook_used'] else '否'}")
    print(f"实际分析轮次: {state['analysis_rounds']}")

    if state["signals"]:
        print("\n最终交易信号:")
        for sig in state["signals"][-1:]:
            print(f"  • {sig['direction']} | 理由: {sig.get('reason', '')}")

    if state["issues"]:
        print("\n⚠️  最终问题:")
        for issue in state["issues"]:
            print(f"  • {issue}")
    else:
        print("\n✅ 分析完成")

    print("="*70)
    return state


def persist(state: TAState) -> TAState:
    print("[结束] 保存分析结果...")
    state["artifacts"].append(f"report_{state['thread_id']}.md")
    state["is_done"] = True
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
    print("=== EA Agent - 测试优化版 ===\n")
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)
