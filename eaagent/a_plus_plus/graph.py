from typing import Literal, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import APlusPlusState, create_initial_state
from .eaagent_wrapper import APlusPlusReActAgent
from .prompt_builder import PlaybookPromptBuilder
from .tools import get_structured_observation


def get_ea_agent() -> APlusPlusReActAgent:
    agent = APlusPlusReActAgent()
    agent.load_playbook()
    return agent


def _get_message_content(msg: Any) -> str:
    if isinstance(msg, dict):
        return msg.get("content", "")
    return getattr(msg, "content", "")


def tools_node(state: APlusPlusState) -> APlusPlusState:
    """
    多时间框架工具节点（支持优雅降级）
    - 优先获取日线（必须）
    - 尝试获取30分钟（可选，失败则降级）
    """
    symbol = state.get("current_symbol", "RB2605")

    # 1. 获取日线（核心数据）
    daily_obs = get_structured_observation(symbol, period="D")

    # 2. 尝试获取30分钟（可选）
    try:
        min30_obs = get_structured_observation(symbol, period="30")
        min30_text = min30_obs.get('observation_text', '')
        min30_available = True
    except Exception as e:
        min30_text = f"【30分钟数据获取失败】{str(e)[:80]}"
        min30_available = False

    # 3. 组合 Observation
    if min30_available:
        combined = f"""【日线观察 - 大趋势】
{daily_obs.get('observation_text', '')}

【30分钟观察 - 结构与入场】
{min30_text}
"""
    else:
        combined = f"""【日线观察 - 大趋势】
{daily_obs.get('observation_text', '')}

【30分钟观察】
{min30_text}
（系统已自动降级，仅使用日线数据进行分析）
"""

    state["messages"].append({
        "role": "system",
        "content": f"【工具返回的多时间框架 Observation】\n{combined}"
    })

    state["last_observation"] = {
        "daily": daily_obs,
        "30min": min30_obs if min30_available else None,
        "30min_available": min30_available
    }

    state["next_action"] = "ea_reasoning"
    return state


def ea_reasoning_node(state: APlusPlusState) -> APlusPlusState:
    messages = state.get("messages", [])
    goal = _get_message_content(messages[-1]) if messages else ""

    rag_context = state.get("rag_context")
    playbook_builder = PlaybookPromptBuilder()
    enhanced_prompt = playbook_builder.build_system_prompt(rag_context=rag_context)
    full_goal = f"{enhanced_prompt}\n\n当前任务：{goal}"

    ea_agent = get_ea_agent()
    result = ea_agent.run(full_goal)

    state["messages"].append({"role": "assistant", "content": result})
    state["next_action"] = "reflection"
    return state


def reflection_node(state: APlusPlusState) -> APlusPlusState:
    messages = state.get("messages", [])
    last_assistant_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            last_assistant_msg = msg.get("content", "")
            break

    reflection_parts = ["【自我反思】"]

    last_obs = state.get("last_observation", {})
    if last_obs.get("30min_available") is False:
        reflection_parts.append("⚠️ 30分钟数据获取失败，已自动降级为仅使用日线分析。")
    elif "日线观察" in last_assistant_msg and "30分钟观察" in last_assistant_msg:
        reflection_parts.append("✅ 成功结合日线趋势 + 30分钟结构进行分析。")

    if any(kw in last_assistant_msg for kw in ["量仓", "持仓量", "成交量变化"]):
        reflection_parts.append("✅ 关注了量仓变化，符合 Playbook 核心逻辑。")
    else:
        reflection_parts.append("⚠️ 建议加入量仓变化的观察。")

    if any(kw in last_assistant_msg for kw in ["主动放弃", "暂不", "保持观望", "信息不足"]):
        reflection_parts.append("✅ 体现了信息不足时主动放弃/观望的意识。")

    reflection = "\n".join(reflection_parts)
    reflection += "\n\n建议：继续保持多时间框架分析 + 量仓逻辑的风格。"

    state["reflection_notes"] = reflection
    state["messages"].append({"role": "system", "content": reflection})
    state["next_action"] = "human_feedback"
    return state


def human_feedback_node(state: APlusPlusState) -> APlusPlusState:
    state["interrupt_reason"] = "等待人类反馈确认或修正建议"
    return state


def should_continue(state: APlusPlusState) -> Literal["ea_reasoning", "reflection", "end"]:
    next_action = state.get("next_action", "end")
    if next_action == "ea_reasoning":
        return "ea_reasoning"
    elif next_action == "reflection":
        return "reflection"
    else:
        return "end"


def build_graph():
    workflow = StateGraph(APlusPlusState)

    workflow.add_node("tools", tools_node)
    workflow.add_node("ea_reasoning", ea_reasoning_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("human_feedback", human_feedback_node)

    workflow.set_entry_point("tools")

    workflow.add_conditional_edges(
        "tools",
        should_continue,
        {
            "ea_reasoning": "ea_reasoning",
            "reflection": "reflection",
            "end": END,
        }
    )

    workflow.add_edge("ea_reasoning", "reflection")
    workflow.add_edge("reflection", "human_feedback")
    workflow.add_edge("human_feedback", END)

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    return app


if __name__ == "__main__":
    app = build_graph()
    state = create_initial_state()
    state["current_symbol"] = "RB2605"
    state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]

    config = {"configurable": {"thread_id": "test-001"}}
    result = app.invoke(state, config)
    print(result["messages"][-1])
