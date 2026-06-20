"""
Mock LLM 的集成测试 - graph 模块
"""
import os
os.environ.setdefault("USE_MOCK_LLM", "true")

import pytest
from eaagent.a_plus_plus.graph import (
    create_initial_state,
    build_graph,
)


def test_full_graph_execution():
    """ 测试完整流程（使用 mock LLM） """
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    config = {"configurable": {"thread_id": state["thread_id"]}}

    result = app.invoke(state, config)

    assert result["current_symbol"] == "RB2605.SHF"
    assert result["is_done"] is True
    assert result["analysis_rounds"] >= 1


def test_graph_has_persistence():
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    thread_id = state["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    result1 = app.invoke(state, config)
    assert result1["is_done"] is True

    result2 = app.invoke({"messages": []}, config)
    assert result2 is not None


def test_playbook_strategy_is_logged_during_execution(capfd):
    """
    验证在 graph 执行过程中，日志中是否输出了当前 Playbook 策略信息。
    """
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    config = {"configurable": {"thread_id": state["thread_id"]}}

    result = app.invoke(state, config)

    captured = capfd.readouterr()
    output = captured.out

    assert any(
        kw in output.lower()
        for kw in ["playbook", "策略", "core", "full"]
    ), "执行过程中应输出当前使用的 Playbook 策略信息"
