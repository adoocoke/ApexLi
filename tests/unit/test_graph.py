"""
纯单元测试 - graph 模块（不依赖 LLM）
"""
from eaagent.a_plus_plus.graph import (
    create_initial_state,
    quality_sensor,
    signal_generation,
    TAState,
)


def test_create_initial_state():
    state = create_initial_state("RB2605.SHF")
    assert state["current_symbol"] == "RB2605.SHF"
    assert state["max_rounds"] == 5
    assert state["iteration"] == 0


def test_quality_sensor_detects_issues():
    state: TAState = create_initial_state("TEST")
    state["iteration"] = 1
    state["observations"] = [{"llm_observation": "测试观察"}]
    state["confidence"] = 0.6

    result = quality_sensor(state)
    assert len(result["issues"]) >= 1


def test_signal_generation_node():
    state: TAState = create_initial_state("TEST")
    state["iteration"] = 1
    state["observations"] = [{"llm_observation": "测试观察"}]

    result = signal_generation(state)

    assert len(result["signals"]) >= 1
    assert result["iteration"] == 1
