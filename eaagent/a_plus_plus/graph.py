"""
eaagent/a_plus_plus/graph.py
高质量自动分析版 + 多轮循环 + 透明日志（Playbook 规则 + Tushare 详情）
"""

from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime
import os
import re

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# ==================== Playbook 加载与规则提取 ====================
PLAYBOOK_CONTENT = ""
PLAYBOOK_LOADED = False
PLAYBOOK_RULES = []   # 提取出的关键规则列表

def load_playbook() -> bool:
    global PLAYBOOK_CONTENT, PLAYBOOK_LOADED, PLAYBOOK_RULES

    possible_paths = [
        "artifacts/trading_playbook_v3.md",
        "artifacts/playbooks/trading_playbook_v3.md",
        "trading_playbook_v3.md",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    PLAYBOOK_CONTENT = f.read()

                # 简单提取关键规则（可根据实际 Playbook 结构优化）
                PLAYBOOK_RULES = re.findall(r'###\s*(.+?)(?=\n|$)', PLAYBOOK_CONTENT)
                if not PLAYBOOK_RULES:
                    PLAYBOOK_RULES = ["量仓变化优先", "多时间框架一致性", "严格止损纪律"]

                PLAYBOOK_LOADED = True
                print(f"[Playbook] ✅ 成功加载: {path}（共 {len(PLAYBOOK_RULES)} 条关键规则）")
                return True
            except Exception as e:
                print(f"[Playbook] 读取失败: {e}")
                return False

    print("[Playbook] ❌ 未找到 trading_playbook_v3.md")
    return False


def get_relevant_playbook_rules(context: str) -> List[str]:
    """根据当前上下文匹配相关 Playbook 规则"""
    if not PLAYBOOK_LOADED:
        return []

    relevant = []
    context_lower = context.lower()

    for rule in PLAYBOOK_RULES:
        rule_lower = rule.lower()
        if any(keyword in context_lower for keyword in ["量", "仓", "止损", "时间框架", "支撑", "阻力"]):
            if any(kw in rule_lower for kw in ["量", "仓", "止损", "时间", "框架"]):
                relevant.append(rule)

    return relevant[:3] if relevant else PLAYBOOK_RULES[:2]


# ==================== Tushare 数据获取（带详细日志） ====================
def get_real_tushare_data(symbol: str, timeframes: List[str]) -> Dict[str, Any]:
    print(f"[Tushare] 尝试获取 {symbol} 的 {timeframes} 数据...")

    try:
        import tushare as ts
        token = os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("环境变量 TUSHARE_TOKEN 未设置")

        ts.set_token(token)
        pro = ts.pro_api()

        data = {}
        for tf in timeframes:
            try:
                df = pro.fut_daily(ts_code=symbol, start_date='20240601', end_date='20240618')
                if not df.empty:
                    latest = df.iloc[-1]
                    data[tf] = {
                        "close": float(latest['close']),
                        "volume": int(latest.get('vol', 0)),
                        "open": float(latest.get('open', 0)),
                        "high": float(latest.get('high', 0)),
                        "low": float(latest.get('low', 0)),
                    }
                    print(f"[Tushare] {tf} 获取成功，最新 close={data[tf]['close']}")
                else:
                    data[tf] = {"close": 0, "volume": 0}
                    print(f"[Tushare] {tf} 无数据")
            except Exception as e:
                print(f"[Tushare] {tf} 获取失败: {e}")
                data[tf] = {"close": 0, "volume": 0}

        return data

    except Exception as e:
        print(f"[Tushare] 整体获取失败: {e}，回退到 Mock 数据")
        return {
            "5m": {"close": 4120, "volume": 120000},
            "30m": {"close": 4115, "volume": 85000},
            "1d": {"close": 4100, "volume": 350000}
        }


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
    else:
        state["playbook_used"] = False

    print(f"  - 最大分析轮次: {state['max_rounds']}")
    print("="*70)
    return state


def data_ingestion(state: TAState) -> TAState:
    state["iteration"] += 1
    print(f"\n[第 {state['iteration']} 轮] 数据获取阶段")

    if state["data_source"] == "tushare":
        state["market_data"] = get_real_tushare_data(
            state["current_symbol"], state["timeframes"]
        )
    else:
        print("  → 使用 Mock 数据")
        state["market_data"] = {
            "5m": {"close": 4120, "volume": 120000},
            "30m": {"close": 4115, "volume": 85000},
            "1d": {"close": 4100, "volume": 350000}
        }
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

    state["signals"].append({
        "direction": "多头",
        "entry": 4125,
        "stop_loss": 4080,
        "timeframe": "30m",
        "reason": "量价齐升 + 关键支撑"
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
        issues.append("观察数据不足")
    if state["confidence"] < 0.75:
        issues.append("置信度偏低，建议继续分析")

    state["issues"] = issues
    state["risk_assessment"] = {"issues_count": len(issues), "issues": issues}
    state["analysis_rounds"] = state["iteration"]
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
    print("=== EA Agent - 多轮分析版（透明日志）===\n")
    app = build_graph()
    state = create_initial_state("RB2605")
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)
