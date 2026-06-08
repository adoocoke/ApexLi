from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import APlusPlusState, create_initial_state
from .eaagent_wrapper import APlusPlusReActAgent
from .prompt_builder import PlaybookPromptBuilder


def get_ea_agent() -> APlusPlusReActAgent:
    """延迟初始化，避免模块级报错"""
    agent = APlusPlusReActAgent()
    agent.load_playbook()
    return agent


def ea_reasoning_node(state: APlusPlusState) -> APlusPlusState:
    """核心推理节点"""
    goal = state.get("messages", [])[-1].content if state.get("messages") else ""
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
    """工具调用节点（占位，后续扩展）"""
    state["messages"].append({"role": "system", "content": "[工具节点] 已执行工具调用"})
    state["next_action"] = "reflection"
    return state


def reflection_node(state: APlusPlusState) -> APlusPlusState:
    """自我反思节点"""
    last_response = state["messages"][-1]["content"] if state.get("messages") else ""
    reflection = f"【自我反思】上一步输出：{last_response[:200]}...\n需要检查是否符合 Playbook 风格。"
    state["reflection_notes"] = reflection
    state["messages"].append({"role": "system", "content": reflection})
    state["next_action"] = "human_feedback"
    return state


def human_feedback_node(state: APlusPlusState) -> APlusPlusState:
    """人类反馈节点"""
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
    """构建 A++ LangGraph 工作流"""
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
    initial_state = create_initial_state()
    initial_state["messages"] = [{"role": "user", "content": "请分析当前铁矿走势"}]
    result = app.invoke(initial_state)
    print(result["messages"][-1])
