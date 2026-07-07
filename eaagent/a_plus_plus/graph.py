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
    from .nodes.llm_critique import llm_critique
    from .nodes.observation import structured_observation
    from .nodes.quality_sensor import quality_sensor
    from .utils.console import color_print, Colors
    from .utils.llm import call_llm
    return (MemorySaver, StateGraph, END, TAState, manager, MAX_ROUNDS, persist, data_ingestion, data_gathering, 
            llm_critique, structured_observation, quality_sensor, color_print, Colors, call_llm)

# Global lazy objects
_MemorySaver, _StateGraph, _END, TAState, manager, MAX_ROUNDS, persist, data_ingestion, data_gathering, llm_critique, structured_observation, quality_sensor, color_print, Colors, call_llm = _lazy_import_graph()


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

    # 结构化prompt - 最小文字入侵，核心规则/输出要求/操作组纪律/Few-shot全部来自Playbook (manager.build_prompt)
    playbook_content = manager.build_prompt(cur_playbook, max_chars=3500)
    prompt = f"""你是一个严格遵守 **当前{cur_playbook} Playbook** 的期货交易决策者。**基于完整K线历史 (5-12个月) + 工具 + 视觉结果**，一次性分析整段K线，输出**所有**高置信买卖点（趋势全生命周期）。严格只使用当前{cur_playbook}章节，禁止混用。

**当前Playbook完整规则（含第0节输出要求、操作组纪律、JSON Few-shot）**：
{playbook_content}

基于以下观察（含visual_signals）：
{obs}

**任务**：按Playbook要求输出JSON。视觉/K线匹配规则才输出signal（含精确日期、引用前缀"引用{cur_playbook}-X.Y"、conf>=80）。无匹配只观望。有依据就标记买卖/平仓（操作组：买入/买平、卖出/卖平为一组，破规则必须平仓）。覆盖趋势开启到结束。

只输出JSON，无额外文字。

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

    基于以下结构化市场观察（已包含完整5-12个月K线数据），请**一次性分析整段K线**，输出**所有高置信买卖点**（趋势开启、背驰、定式确认等位置）。有明确**当前{cur_playbook} Playbook**规则匹配就标记买卖点，无明确依据的区间才观望。

    {obs}

    【输出要求 - 必须严格遵守】

    1. **输出多个signal**：基于整段K线历史，找出**所有符合当前{cur_playbook} Playbook的买卖点**（而非只当前最后一根K线）。每个signal对应一个具体K线位置。

    2. `reason` 字段必须同时包含：
       - **明确出自当前Playbook的章节/规则编号**（**必须以“引用{cur_playbook}-X.Y”开头**, e.g. "引用v3-2.1量仓分析核心逻辑" 或 "引用zen-2.1趋势背驰", **严格禁止混用zen和v3概念**）。
       - **具体哪根K线**为什么匹配这条规则的具体逻辑解释（结合历史数据 + 工具结果 + 量仓/背驰/定式）。
       - **一个分析只能出自相同的Playbook**（当前Web选择的{cur_playbook}），所有signal的reason必须一致引用同一个Playbook章节。

    3. **基于 Playbook 的信号要求**（LLM 必须从**当前{cur_playbook} Playbook**规则中推导，而非硬编码或混用其他Playbook概念）：
       - **买入/买平是一组操作**：买入后如果破了规则（背驰结束、持仓不再增加、定式失效）→ 必须输出“买平”。
       - **卖出/卖平是一组操作**：卖出后如果破了规则 → 必须输出“卖平”。
       - **趋势/仓位 signal** (`trend_signal` / `position_action`)：基于**当前{cur_playbook} Playbook**趋势判断规则，判断**趋势开启到结束**的全生命周期：
         - 下跌趋势**开启**（量仓确认、形态成立）→ “卖出(趋势开启)/做空”。
         - 下跌趋势**结束/震荡**（背驰、持仓不再增加、定式失效）→ “卖平(趋势结束)/观望”。
         - 上涨趋势**开启**（量仓确认、形态成立）→ “买入(趋势开启)/做空”。
         - 上涨趋势**结束/震荡**（背驰、持仓不再增加、定式失效）→ “买平(趋势结束)/观望”。
       - **有依据就标记**：如果K线位置匹配**当前{cur_playbook} Playbook**任何规则，必须输出对应signal + 详细reason（含Playbook章节）；**只有完全无匹配时才输出观望**。
       - **止损**：买入止损，前一个k线的低点，卖出止损前一根k线的高点。
       - 所有 signal 必须**严格引用当前{cur_playbook}具体章节**（e.g. “引用v3-2.1量仓分析核心逻辑：...” 或 “引用zen-2.2背驰判断：...”），并结合完整K线历史 + 工具数据给出**明确逻辑**。**只有有明确Playbook规则匹配才输出signal**；**像index 5678这种无明确原因/规则匹配的绝不能输出为signal**，必须归为“观望” + reason说明“无Playbook依据”。**禁止在一次分析中混用zen和v3概念**。

    4. 输出必须严格按照以下 JSON 格式返回（不要有任何额外文字，输出**signal列表**，每个signal对应一个K线位置）：

    {{
      "signals": [
        {{
          "direction": "多头 / 空头 / 观望",
          "trend_signal": "卖出(趋势开启) / 卖平(趋势结束) /买入(趋势开启) / 买平(趋势结束) / 持仓 / 观望",
          "entry_zone": "入场区间描述（或无）",
          "stop_loss": "止损描述（或无）",
          "target": "目标 / 减仓区间（或无）",
          "reason": "引用了规则X（Playbook具体标题）：在第N根K线位置，价格... + 历史数据 + 工具结果匹配该规则的具体逻辑...（必须包含规则引用 + 具体K线位置）",
          "confidence": 85
        }},
        ... (更多signal)
      ]
    }}

    【Few-shot 示例】（基于完整K线一次性输出多个signal）

    示例1（多个买卖点）：
    {{
      "signals": [
        {{
          "direction": "空头",
          "trend_signal": "卖出(趋势开启)",
          "reason": "引用v3-2.1量仓分析核心逻辑（当前Playbook v3）：在第45根K线位置，价格持续回落同时持仓稳步增加，符合‘持仓增加提供趋势燃料’规则，holding工具确认主力增仓，因此在该位置给出卖出(趋势开启) signal。",
          "confidence": 88
        }},
        {{
          "direction": "观望",
          "trend_signal": "卖平(趋势结束)",
          "reason": "引用v3-2.3趋势判断与行情选择（当前Playbook v3）：在第120根K线位置，出现背驰 + 持仓不再放大，趋势进入结束/震荡阶段，符合‘趋势结束时主动卖平仓位’规则，因此给出卖平 signal (买入/买平或卖出/卖平为一组操作, 破规则后必须平仓; index 5678这类无明确规则匹配的必须观望, 绝不输出为signal)。",
          "confidence": 85
        }}
      ]
    }}

    请严格按照以上要求输出 JSON（**基于完整K线数据一次性输出所有买卖点**，有Playbook规则匹配就标记，无明确依据才观望）。
    """

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    print(f"[SignalGen] LLM response received (type: {type(response)}, len: {len(str(response)) if response else 0})")

    try:
        if not isinstance(response, str) or not response.strip():
            response = '{"signals": []}'  # safe default to prevent NoneType
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            signal_data = json.loads(json_match.group(0))
        else:
            signal_data = json.loads(response)
        # 确保趋势相关字段存在（兼容旧输出 + Playbook 推导）
        if isinstance(signal_data, dict):
            if "trend_signal" not in signal_data:
                signal_data["trend_signal"] = signal_data.get("direction", "观望")
            if "position_action" not in signal_data:
                signal_data["position_action"] = signal_data.get("trend_signal", signal_data.get("direction", "观望"))
    except Exception as e:  # Catch all (JSONDecodeError, TypeError for None, etc.)
        print(f"[SignalGen] JSON parse failed: {type(e).__name__}: {e}. Raw preview: {str(response)[:150] if response else 'None'}")
        signal_data = {
            "direction": "观望",
            "trend_signal": "观望",
            "position_action": "空仓(震荡)",
            "entry_zone": "解析失败",
            "stop_loss": "解析失败",
            "target": "解析失败",
            "reason": str(response) if response else "LLM returned None - using visual signals from observation",
            "confidence": 60
        }

    # If visual_signals already in state from observation, prefer them (Phase 3 vision upgrade)
    if not state.get("signals") and state.get("observations"):
        last_obs = state["observations"][-1]
        if last_obs.get("visual_signals"):
            print(f"[SignalGen] Using visual_signals from observation (4 signals)")
            state["signals"] = last_obs["visual_signals"]
            signal_data = last_obs["visual_signals"][0] if last_obs["visual_signals"] else signal_data

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