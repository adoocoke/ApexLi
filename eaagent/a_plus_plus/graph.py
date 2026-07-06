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
        critique_scores=[],  # Phase 3: Dashboard 柱状图/Mermaid + report_builder
        reason_count=0,
        playbook_id="",
        playbook_content_sent=False,
        interrupt_reason=None,  # Phase 3: human intervention hook
        feedback_log=[],
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

    prompt = f"""你是一个严格遵守 Playbook 的期货交易决策者。**基于完整5-12个月历史数据 + 工具结果**，生成**单笔高置信交易信号**（非每个K线决策）。优先使用工具获取最新数据后再决策。

可用工具 (必须用 tool call 格式调用)：
- get_futures_holding(ts_code): 持仓排名 (强烈推荐用于主力分析)
- get_futures_basic(exchange): 合约基本信息和主力列表
- get_related_futures_dynamic(symbol): 动态相关品种数据 (RB→I/JM, SA→FG/SH)
- get_futures_news(symbol, limit=5): 重要新闻/宏观政策 (驱动基本面)
- generate_kline_chart(symbol): K线图

**工具使用理由**：
- **News/Holding**：捕捉政策、主力仓位变化（增仓=趋势燃料），避免纯技术分析。
- **Related/Basic**：验证联动 + 合约规格/流动性。
- 如果5个月数据不足，请求 "longer_history" (12个月)。

如果需要工具但未提供, 输出 "NEED_TOOL: tool_name (reason for analysis)"。

    【当前 Playbook】
    {manager.build_prompt(cur_playbook)}

    基于以下结构化市场观察（已包含5-12个月数据），请给出**单笔高置信交易信号**：

    {obs}

    【输出要求 - 必须严格遵守】

    1. `reason` 字段必须同时包含：
       - 明确引用 Playbook 的哪一条或哪几条规则（写出完整标题）
       - 当前行情**为什么匹配**这条规则的具体逻辑解释（结合历史数据 + 工具结果）

    2. **趋势跟踪要求**（两个独立要求，不冲突）：
       - **当日 signal**：当前 K 线/观察的即时 direction（多/空/观望）。
       - **趋势 signal**：判断**当前趋势开启到结束**（e.g. 下跌趋势开启时给出“卖出/做空” signal，在趋势结束/震荡时给出“卖平/平仓/观望” signal）。使用 5-12个月历史 + 工具数据判断趋势阶段（phase + trend.mid_term + volume_oi_linkage）。

    3. 输出必须严格按照以下 JSON 格式返回（不要有任何额外文字）：

    {{
      "direction": "多头 / 空头 / 观望",  // 当日即时 signal
      "trend_signal": "卖出(趋势开启) / 卖平(趋势结束/震荡) / 持仓 / 观望",  // 新增：完整趋势判断
      "entry_zone": "入场区间描述（或无）",
      "stop_loss": "止损描述（或无）",
      "target": "目标 / 减仓区间（或无）",
      "reason": "引用了规则X：...（必须包含规则引用 + 历史数据/工具匹配逻辑 + 当日signal + 趋势signal判断）",
      "confidence": 85
    }}

    【Few-shot 示例】（同时满足当日 + 趋势 signal）

    示例1（趋势下跌中）：
    {{
      "direction": "空头",
      "trend_signal": "卖出(趋势开启)",
      "reason": "引用2.1量仓分析核心逻辑：12个月历史价格持续回落同时持仓稳步增加，符合‘持仓增加提供趋势燃料’的规则，当前空头力量占优（holding工具确认）；趋势处于下跌开启阶段，因此给出卖出signal（趋势signal）。当日即时方向也为空头。",
      "confidence": 88
    }}

    示例2（趋势结束/震荡）：
    {{
      "direction": "观望",
      "trend_signal": "卖平(趋势结束)",
      "reason": "引用2.3趋势判断与行情选择：5-12个月历史显示下跌趋势已持续，但出现背驰 + 持仓不再增加，趋势进入结束/震荡阶段，符合‘趋势结束时卖平仓位’规则。因此给出卖平 trend_signal，当日即时 signal 为观望。",
      "confidence": 85
    }}

    请严格按照以上要求输出 JSON（同时提供当日 direction 和趋势 trend_signal）。
    """

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    try:
        signal_data = json.loads(response)
        # 确保 trend_signal 字段存在（兼容旧输出）
        if "trend_signal" not in signal_data:
            signal_data["trend_signal"] = signal_data.get("direction", "观望")
    except json.JSONDecodeError:
        signal_data = {
            "direction": "观望",
            "trend_signal": "观望",
            "entry_zone": "解析失败",
            "stop_loss": "解析失败",
            "target": "解析失败",
            "reason": response,
            "confidence": 60
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
    """Phase 3 增强：支持 human_feedback + 打印完整 prompt/response（已由 llm.py 处理）"""
    color_print(f"\n[第 {state.get('iteration', 1)} 轮] LLM Critique（Grok 审查）", Colors.HEADER)

    # Phase 3: 检查 human intervention
    if state.get("human_feedback"):
        color_print(f"  → 收到人工干预: {state['human_feedback']}", Colors.WARNING)
        state.setdefault("feedback_log", []).append({
            "round": state.get("iteration", 1),
            "feedback": state["human_feedback"],
            "timestamp": datetime.now().isoformat()
        })

    prompt = f"""你是一个严格且专业的交易策略风险审查员。根据当前信息**自主决定是否需要继续多轮分析**（不再强制任何固定轮次）。如果数据已充分（置信度>85%、信号一致、无新风险/矛盾、工具数据足够），直接 should_continue=false 结束分析；否则继续调用工具获取更多持仓/新闻/相关品种数据。

当前轮次信息：
- 轮次: {state.get('iteration', 1)} / MAX=5
- 置信度: {state.get('confidence', 0.6):.0%}
- 本轮发现的问题: {state.get('issues', [])}
- 本轮交易信号: {state.get('signals', [{}])[-1] if state.get('signals') else '无'}
- 本轮结构化观察摘要: {state.get('observations', [{}])[-1] if state.get('observations') else '无'}
- 人工反馈: {state.get('human_feedback', '无')}

请严格按照以下 JSON 格式返回（不要有任何额外文字）：
{{
  "should_continue": true/false,
  "reason": "是否继续下一轮的理由（明确说明数据是否充分或需要更多工具调用）",
  "comparison_summary": "前后轮对比的核心结论",
  "risk_change": "上升 / 下降 / 不变",
  "score": 85,  // 0-100 Critique 评分 (用于 Dashboard 柱状图和报告)
  "key_rules": ["2.1 量仓分析", "3.1 背驰判断"]  // 主要规则 (真实数据)
}}"""

    system_prompt = state.get("messages", [{}])[0].get("content", "") if state.get("messages") else ""
    response = call_llm(prompt, system_prompt)  # llm.py 会打印 [LLM Prompt] + [Grok Response]

    state["critique_result"] = {"raw_response": response, "has_previous_round": len(state.get("observations", [])) >= 1}

    # Phase 3: 解析真实 score/key_rules 到 state
    try:
        import json, re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            score = int(data.get("score", 85))
            rules = data.get("key_rules", ["规则匹配"])
            state.setdefault("critique_scores", []).append(score)
            state["critique_result"]["score"] = score
            state["critique_result"]["key_rules"] = rules
            color_print(f"  → Critique 评分: {score} | 关键规则: {rules[:2]}", Colors.OKGREEN)
    except Exception as e:
        state.setdefault("critique_scores", []).append(85)
        color_print(f"  → JSON 解析失败，使用默认评分 85: {e}", Colors.WARNING)

    return state


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

    # 让 LLM 完全决定轮次（移除强制 <4 轮）
    try:
        import json, re
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            should_continue = result.get("should_continue", False)
            reason = result.get("reason", "")
            color_print(f"  → LLM 决定: should_continue={should_continue} | {reason}", Colors.OKCYAN)
            return "continue" if should_continue else "finalize"
    except Exception as e:
        color_print(f"  → JSON 解析失败，默认结束: {e}", Colors.WARNING)
        pass

    # LLM 未明确返回时，默认基于置信度/问题结束（避免无限循环）
    if state.get("confidence", 0) > 0.85 and not state.get("issues"):
        return "finalize"
    return "finalize"  # 默认结束，让 LLM 主导

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

    # 关键引用规则一览 (structured from Step 2 EA-002)
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