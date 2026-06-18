"""
测试 eaagent.a_plus_plus.graph 模块
运行命令: pytest tests/test_graph.py -v
"""

import pytest
from eaagent.a_plus_plus.graph import (
    create_initial_state,
    build_graph,
    TAState,
)


def test_create_initial_state():
    """测试初始状态创建"""
    state = create_initial_state("RB2605")
    
    assert state["current_symbol"] == "RB2605"
    assert state["thread_id"].startswith("ta-RB2605-")
    assert state["iteration"] == 0
    assert state["is_done"] is False
    assert isinstance(state["issues"], list)
    assert isinstance(state["signals"], list)


def test_full_graph_execution():
    """测试完整 graph 是否能正常跑完"""
    app = build_graph()
    state = create_initial_state("RB2605")
    config = {"configurable": {"thread_id": state["thread_id"]}}

    result = app.invoke(state, config)

    # 基本断言
    assert result["current_symbol"] == "RB2605"
    assert result["is_done"] is True
    assert len(result["signals"]) > 0
    assert result["confidence"] > 0
    assert isinstance(result["issues"], list)


def test_quality_sensor_detects_issues():
    """测试 quality_sensor 能否正确发现问题"""
    app = build_graph()
    state = create_initial_state("TEST")
    config = {"configurable": {"thread_id": state["thread_id"]}}

    # 故意让数据不足
    result = app.invoke(state, config)

    # 因为我们目前 observation 只有1条，sensor 应该检测到问题
    assert len(result["issues"]) >= 1
    # 可以根据实际逻辑调整断言
    # assert any("观察数据不足" in issue for issue in result["issues"])


def test_graph_has_persistence():
    """测试 checkpointer 是否正常工作"""
    app = build_graph()
    state = create_initial_state("RB2605")
    thread_id = state["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    # 第一次运行
    result1 = app.invoke(state, config)
    assert result1["is_done"] is True

    # 第二次使用相同 thread_id 应该能拿到历史状态
    # 这里简单验证 checkpointer 没有报错即可
    result2 = app.invoke({"messages": []}, config)
    assert result2 is not None


def test_signal_generation_node():
    """单独测试 signal_generation 节点逻辑"""
    from eaagent.a_plus_plus.graph import signal_generation

    state: TAState = create_initial_state("TEST")
    result = signal_generation(state)

    assert len(result["signals"]) == 1
    assert result["signals"][0]["direction"] == "多头"
    assert result["confidence"] > 0
    assert result["iteration"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
