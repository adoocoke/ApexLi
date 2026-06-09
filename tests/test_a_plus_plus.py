import os
import pytest

os.environ["USE_MOCK_OBSERVATION"] = "true"

from eaagent.a_plus_plus.tools import get_structured_observation, detect_key_levels
from eaagent.a_plus_plus.prompt_builder import PlaybookPromptBuilder

try:
    from eaagent.a_plus_plus.graph import build_graph, create_initial_state
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestToolsMock:
    """测试工具模块（含优化后的关键位识别）"""

    def test_get_structured_observation_daily(self):
        result = get_structured_observation("RB2605", period="D")
        assert result["status"] == "mock"
        assert "key_levels" in result
        assert "resistances" in result["key_levels"]
        assert "supports" in result["key_levels"]
        assert len(result["key_levels"]["resistances"]) > 0
        assert len(result["key_levels"]["supports"]) > 0
        assert "压力位" in result["observation_text"]
        print("✅ 日线 Observation + 关键位识别 测试通过")

    def test_get_structured_observation_30min(self):
        result = get_structured_observation("RB2605", period="30")
        assert result["status"] == "mock"
        assert "key_levels" in result
        print("✅ 30分钟 Observation 测试通过")


@pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph 未安装，跳过 Graph 测试")
class TestMultiTimeframeGraph:
    def test_graph_multi_timeframe(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]
        config = {"configurable": {"thread_id": "test-mtf-001"}}
        result = app.invoke(state, config)
        assert result is not None
        print("✅ 多时间框架 Graph 测试通过")


class TestPromptBuilder:
    def test_playbook_loaded(self):
        builder = PlaybookPromptBuilder()
        if "警告" in builder.playbook_content:
            pytest.skip("Playbook 文件未找到，跳过检查")
        assert len(builder.playbook_content) > 1000
        print("✅ Playbook 加载测试通过")


if __name__ == "__main__":
    print("=== 开始测试 ===\n")
    TestToolsMock().test_get_structured_observation_daily()
    TestToolsMock().test_get_structured_observation_30min()
    if HAS_LANGGRAPH:
        TestMultiTimeframeGraph().test_graph_multi_timeframe()
    TestPromptBuilder().test_playbook_loaded()
    print("\n=== 测试完成 ===")
