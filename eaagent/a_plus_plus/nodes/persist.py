from eaagent.a_plus_plus.types import TAState


def persist(state: TAState) -> TAState:
    print("[结束] 保存分析结果...")
    state["artifacts"].append(f"report_{state['thread_id']}.md")
    state["is_done"] = True
    return state
