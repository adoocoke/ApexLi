"""
eaagent/a_plus_plus/graph.py
高质量自动分析版 Harness（选项 A）
默认全自动 + 强 Sensors + 清晰输出 + 可选 HITL
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


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
    issues: List[str]                    # Sensors 发现的问题
    verification_result: Optional[dict]
    human_feedback: Optional[str]
    iteration: int
    is_done: bool
    created_at: datetime
    last_updated: datetime


def create_initial_state(symbol: str = "RB2605") -> TAState:
    now = datetime.now()
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
    )


# ==================== 节点 ====================
def initialize_state(state: TAState) -> TAState:
    print(f"\n[Guides] 初始化 {state['current_symbol']} 分析任务...")
    state["iteration"] = 0
    return state


def data_ingestion(state: TAState) -> TAState:
    print(f"[Data] 获取 {state['current_symbol']} 多时间框架数据...")
    # TODO: 替换为真实数据获取
    state["market_data"] = {
        "5m": {"close": 4120, "volume": 120000},
        "30m": {"close": 4115, "volume": 85000},
        "1d": {"close": 4100, "volume": 350000}
    }
    return state


def structured_observation(state: TAState) -> TAState:
    print("[Observation] 执行结构化市场观察...")
    state["observations"].append({
        "volume_position_change": "放量增仓",
        "key_levels": [4080, 4150],
        "atr_status": "正常"
    })
    return state


def signal_generation(state: TAState) -> TAState:
    print("[Signal] 生成交易信号...")
    state["signals"].append({
        "direction": "多头",
        "entry": 4125,
        "stop_loss": 4080,
        "timeframe": "30m",
        "reason": "量价齐升 + 关键支撑"
    })
    state["confidence"] = 0.78
    state["iteration"] += 1
    return state


def quality_sensor(state: TAState) -> TAState:
    """Sensors 层：自动检查问题（不强制中断）"""
    print("[Sensor] 执行质量检查...")
    issues = []

    if state["confidence"] < 0.65:
        issues.append("置信度偏低，建议关注")
    if len(state["observations"]) < 2:
        issues.append("观察数据不足")

    # 示例：多时间框架一致性检查
    if len(state["signals"]) > 1:
        directions = [s["direction"] for s in state["signals"]]
        if len(set(directions)) > 1:
            issues.append("多时间框架信号方向存在冲突")

    state["issues"] = issues
    state["risk_assessment"] = {"issues_count": len(issues), "issues": issues}
    return state


def final_output(state: TAState) -> TAState:
    """生成清晰的最终分析结果"""
    print("\n" + "="*60)
    print(f"【{state['current_symbol']} 技术分析报告】")
    print("="*60)
    print(f"综合置信度: {state['confidence']:.0%}")
    
    if state["signals"]:
        print("\n交易信号:")
        for sig in state["signals"]:
            print(f"  - {sig['direction']} | 入场: {sig['entry']} | 止损: {sig.get('stop_loss', 'N/A')}")
            print(f"    理由: {sig.get('reason', '')}")

    if state["issues"]:
        print("\n⚠️  发现的问题 / 警告:")
        for issue in state["issues"]:
            print(f"  - {issue}")
    else:
        print("\n✅ 未发现明显问题")

    print("\n观察要点:")
    for obs in state["observations"]:
        print(f"  - {obs}")

    print("="*60)
    print("分析完成，可继续追问或保存结果。\n")
    return state


def persist(state: TAState) -> TAState:
    print("[Persist] 保存本次分析结果...")
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
    workflow.add_edge("quality_sensor", "final_output")
    workflow.add_edge("final_output", "persist")
    workflow.add_edge("persist", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


# ==================== 测试入口 ====================
if __name__ == "__main__":
    print("=== EA Agent - 高质量自动分析版 ===\n")

    app = build_graph()
    state = create_initial_state("RB2605")
    config = {"configurable": {"thread_id": state["thread_id"]}}

    result = app.invoke(state, config)

    print("分析已完成，可继续使用相同 thread_id 继续追问。")
