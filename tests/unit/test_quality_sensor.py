"""
纯单元测试 - Quality Sensor
"""
from eaagent.a_plus_plus.graph import quality_sensor, create_initial_state, TAState


def test_quality_sensor_detects_issues():
    state: TAState = create_initial_state("TEST")
    state["iteration"] = 1
    state["observations"] = [{"llm_observation": "测试观察"}]
    state["confidence"] = 0.6

    result = quality_sensor(state)
    assert len(result["issues"]) >= 1
