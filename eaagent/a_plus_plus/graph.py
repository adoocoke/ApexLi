"""
eaagent/a_plus_plus/graph.py
重构后版本 - Harness 核心逻辑
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from eaagent.playbooks.manager import manager
from .config import MAX_ROUNDS
# ==================== 节点模块 ====================
from .nodes import persist, data_ingestion
from .nodes.data_gathering import data_gathering
from .nodes.llm_critique import llm_critique
from .nodes.observation import structured_observation
from .nodes.quality_sensor import quality_sensor
from .types import TAState
from .utils.console import color_print, Colors
# ==================== 工具模块 ====================
from .utils.llm import call_llm


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
        reason_count=0,
        playbook_id="",
        playbook_content_sent=False,
    )


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


def signal_generation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 生成交易信号（Grok 分析）", Colors.OKGREEN)

    obs = state["observations"][-1] if state["observations"] else {}
    cur_playbook = state.get("current_playbook", "v3")
    relevant_rules = manager.get_rules(cur_playbook)

    prompt = f"""你是一个严格遵守 Playbook 的期货交易决策者。可使用以下工具获取额外数据：

可用工具：
- get_futures_holding(ts_code): 持仓排名 (doc_id=290, 强烈推荐用于主力分析)
- get_futures_basic(exchange): 合约基本信息和主力列表
- get_related_futures_dynamic(symbol): 动态相关品种数据 (自动匹配RB→I/JM等)
- generate_kline_chart(symbol): K线图

如果需要工具但未提供, 输出 "NEED_TOOL: tool_name (reason for analysis)"。

    【当前 Playbook】
    {manager.build_prompt(cur_playbook)}

    基于以下结构化市场观察，请给出**结构化交易建议**：

    {obs}

    【输出要求 - 必须严格遵守】

    1. `reason` 字段必须同时包含以下两部分：
       - 明确引用了 Playbook 的哪一条或哪几条规则（写出完整标题）
       - 当前行情**为什么匹配**这条规则的具体逻辑解释

    2. 如果当前行情不符合任何明确交易定式，请输出“观望”，并在 reason 中说明判断依据。

    3. 输出必须严格按照以下 JSON 格式返回（不要有任何额外文字）：

    {{
      "direction": "多头 / 空头 / 观望",
      "entry_zone": "入场区间描述（或无）",
      "stop_loss": "止损描述（或无）",
      "target": "目标 / 减仓区间（或无）",
      "reason": "引用了规则X：当前行情匹配这条规则的原因...（必须包含规则引用 + 匹配逻辑）"
    }}

    【Few-shot 示例】

    示例1（高质量 reason）：
    {{
      "direction": "观望",
      "reason": "引用2.3趋势判断与行情选择：当前虽处于下降趋势，但未出现2B反转、头肩底或颈线突破等明确进场定式，符合‘无明确定式时主动放弃低置信度机会’的规则，因此严格执行观望。"
    }}

    示例2（高质量 reason）：
    {{
      "direction": "空头",
      "reason": "引用2.1量仓分析核心逻辑：价格持续回落同时持仓稳步增加，符合‘持仓增加提供趋势燃料’的规则，当前空头力量占优；同时引用3.1背驰判断标准，MACD柱子面积缩小，出现趋势背驰，因此在压力位附近做空。"
    }}

    请严格按照以上要求输出 JSON。
    """

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
    if state.get("iteration", 0) >= state.get("max_rounds", 5):
        return "finalize"

    critique = state.get("critique_result", {})
    raw_response = critique.get("raw_response", "")

    # 尝试解析 LLM 返回的 JSON
    try:
        import json
        import re as _re
        json_match = _re.search(r"\{.*\}", raw_response, _re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            should_continue = result.get("should_continue", True)
            risk_change = result.get("risk_change", "").lower()

            if should_continue is False:
                return "finalize"
            if risk_change in ["上升", "显著上升", "增加"]:
                return "continue"
            return "continue" if should_continue else "finalize"
    except Exception:
        pass

    # 兜底逻辑
    if "false" in raw_response.lower():
        return "finalize"
    return "continue"

def final_output(state: TAState) -> TAState:
    color_print("\n" + "="*70, Colors.BOLD)
    color_print(f"【{state['current_symbol']} 技术分析报告】（共 {state['analysis_rounds']} 轮）", Colors.BOLD)
    color_print("="*70, Colors.BOLD)

    color_print(f"数据来源: {state['data_source'].upper()}", Colors.OKCYAN)
    color_print(f"Playbook 使用: {'是' if state['playbook_used'] else '否'}", Colors.OKCYAN)
    color_print(f"实际分析轮次: {state['analysis_rounds']}", Colors.OKCYAN)

    # 多轮分析路径总结
    color_print("\n多轮分析路径总结:", Colors.OKBLUE)
    for i, obs in enumerate(state.get("observations", []), 1):
        refs = obs.get("playbook_references", [])
        print(f"  第 {i} 轮: {len(refs)} 条规则引用 | 主要矛盾: {obs.get('main_contradiction', 'N/A')}")

    # 关键引用规则一览 (structured from Step 2)
    color_print("\n关键引用规则一览:", Colors.OKGREEN)
    all_refs = []
    for obs in state.get("observations", []):
        for ref in obs.get("playbook_references", []):
            if isinstance(ref, dict):
                all_refs.append(f"{ref.get('rule', 'N/A')}: {ref.get('match_reason', '')}")
            else:
                all_refs.append(str(ref))
    for r in all_refs[:6]:  # limit for clarity
        print(f"  • {r}")

    if state["signals"]:
        last_signal = state["signals"][-1]
        color_print("\n最终交易信号:", Colors.OKGREEN)
        print(json.dumps(last_signal, ensure_ascii=False, indent=2))

    # 最终决策依据
    color_print("\n最终决策依据:", Colors.OKCYAN)
    print("  • 基于多轮结构化观察 + Playbook 严格匹配")
    print("  • 综合 Sensors/Critique 验证，无明显矛盾")
    if state.get("issues"):
        print("  • 剩余问题:", state["issues"])

    if state["issues"]:
        color_print("\n⚠️  最终问题:", Colors.FAIL)
        for issue in state["issues"]:
            print(f"  • {issue}")
    else:
        color_print("\n✅ 分析完成，未发现明显问题", Colors.OKGREEN)

    color_print("="*70, Colors.BOLD)
    return state


def build_graph():
    workflow = StateGraph(TAState)

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
    workflow.add_edge("persist", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


if __name__ == "__main__":
    color_print("=== EA Agent - Harness 重构版 ===", Colors.BOLD)
    app = build_graph()
    state = create_initial_state("RB2610.SHF", playbook_name="zen")  # ← 改这里测试 zen
    config = {"configurable": {"thread_id": state["thread_id"]}}
    app.invoke(state, config)