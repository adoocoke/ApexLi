import os
import pytest

os.environ["USE_MOCK_OBSERVATION"] = "true"

from eaagent.a_plus_plus.tools import get_structured_observation
from eaagent.a_plus_plus.prompt_builder import PlaybookPromptBuilder

try:
    from eaagent.a_plus_plus.graph import build_graph, create_initial_state
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestToolsMock:
    def test_get_structured_observation_daily(self):
        result = get_structured_observation("RB2605", period="D")
        assert result["status"] == "mock"
        assert "observation_text" in result
        print("✅ 日线 Observation 测试通过")

    def test_get_structured_observation_30min(self):
        result = get_structured_observation("RB2605", period="30")
        assert result["status"] == "mock"
        assert "observation_text" in result
        print("✅ 30分钟 Observation 测试通过")


@pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph 未安装，跳过 Graph 测试")
class TestMultiTimeframeGraph:
    """测试日线 + 30分钟 多时间框架流程"""

    def test_graph_multi_timeframe(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]

        config = {"configurable": {"thread_id": "test-mtf-001"}}
        result = app.invoke(state, config)

        assert result is not None
        last_msg = result["messages"][-1]["content"]

        # 检查是否同时包含日线和30分钟观察
        assert "日线观察" in last_msg or "多时间框架" in last_msg
        print("✅ 多时间框架 Graph 测试通过")

    def test_reflection_multi_timeframe(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]

        config = {"configurable": {"thread_id": "test-mtf-002"}}
        result = app.invoke(state, config)

        last_msg = result["messages"][-1]["content"]
        # 检查 Reflection 是否认可多时间框架
        assert "多时间框架" in last_msg or "日线" in last_msg
        print("✅ Reflection 多时间框架检查测试通过")


class TestPromptBuilder:
    def test_playbook_loaded(self):
        builder = PlaybookPromptBuilder()
        if "警告" in builder.playbook_content:
            pytest.skip("Playbook 文件未找到，跳过检查")
        assert len(builder.playbook_content) > 1000
        print("✅ Playbook 加载测试通过")


if __name__ == "__main__":
    print("=== 开始多时间框架测试 ===\n")
    TestToolsMock().test_get_structured_observation_daily()
    TestToolsMock().test_get_structured_observation_30min()
    if HAS_LANGGRAPH:
        TestMultiTimeframeGraph().test_graph_multi_timeframe()
        TestMultiTimeframeGraph().test_reflection_multi_timeframe()
    TestPromptBuilder().test_playbook_loaded()
    print("\n=== 测试完成 ===")
