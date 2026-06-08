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
    state["next_action"] = "tool" if "Action" in result else "end"
    return state


def tools_node(state: APlusPlusState) -> APlusPlusState:
    symbol = state.get("current_symbol", "RB2605")   # 默认使用更稳定的合约
    period = state.get("current_timeframe", "D")

    try:
        obs = get_structured_observation(symbol=symbol, period=period)
        observation_text = obs.get("observation_text", str(obs))
    except Exception as e:
        observation_text = f"获取 {symbol} 结构化数据失败: {str(e)}"

    state["messages"].append({
        "role": "system",
        "content": f"【工具返回的结构化 Observation】\n{observation_text}"
    })
    state["last_observation"] = obs if 'obs' in locals() else {"status": "error"}
    state["next_action"] = "reflection"
    return state


def reflection_node(state: APlusPlusState) -> APlusPlusState:
    messages = state.get("messages", [])
    last_content = _get_message_content(messages[-1]) if messages else ""
    reflection = f"【自我反思】上一步输出：{last_content[:400]}...\n需检查是否符合 Playbook 中的量仓逻辑、定式与风险控制。"
    state["reflection_notes"] = reflection
    state["messages"].append({"role": "system", "content": reflection})
    state["next_action"] = "human_feedback"
    return state


def human_feedback_node(state: APlusPlusState) -> APlusPlusState:
    state["interrupt_reason"] = "等待人类反馈确认或修正建议"
    return state


def should_continue(state: APlusPlusState) -> Literal["tools", "reflection", "end"]:
    next_action = state.get("next_action", "end")
    if next_action == "tool":
        return "tools"
    elif next_action == "reflection":
        return "reflection"
    else:
        return "end"


def build_graph():
    workflow = StateGraph(APlusPlusState)

    workflow.add_node("ea_reasoning", ea_reasoning_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("human_feedback", human_feedback_node)

    workflow.set_entry_point("ea_reasoning")

    workflow.add_conditional_edges(
        "ea_reasoning",
        should_continue,
        {
            "tools": "tools",
            "reflection": "reflection",
            "end": END,
        }
    )

    workflow.add_edge("tools", "reflection")
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
