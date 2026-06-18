"""
测试 eaagent.a_plus_plus.graph 模块
"""

import pytest
from eaagent.a_plus_plus.graph import (
    create_initial_state,
    build_graph,
    signal_generation,
    quality_sensor,
    TAState,
)


def test_create_initial_state():
    state = create_initial_state("RB2605.SHF")
    assert state["current_symbol"] == "RB2605.SHF"
    assert state["max_rounds"] == 5
    assert state["iteration"] == 0


def test_full_graph_execution():
    """测试完整流程是否能正常运行"""
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    config = {"configurable": {"thread_id": state["thread_id"]}}

    result = app.invoke(state, config)

    assert result["current_symbol"] == "RB2605.SHF"
    assert result["is_done"] is True
    assert result["analysis_rounds"] >= 1


def test_quality_sensor_detects_issues():
    """测试 quality_sensor 能检测到问题"""
    state: TAState = create_initial_state("TEST")
    state["iteration"] = 1
    state["observations"] = [{"llm_observation": "测试观察"}]
    state["confidence"] = 0.6

    result = quality_sensor(state)
    assert len(result["issues"]) >= 1


def test_signal_generation_node():
    """测试 signal_generation 节点"""
    state: TAState = create_initial_state("TEST")
    state["iteration"] = 1
    state["observations"] = [{"llm_observation": "测试观察"}]

    result = signal_generation(state)

    assert len(result["signals"]) >= 1
    assert result["iteration"] == 1


def test_graph_has_persistence():
    """测试持久化功能"""
    app = build_graph()
    state = create_initial_state("RB2605.SHF")
    thread_id = state["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    result1 = app.invoke(state, config)
    assert result1["is_done"] is True

    result2 = app.invoke({"messages": []}, config)
    assert result2 is not None
