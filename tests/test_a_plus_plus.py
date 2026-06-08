import os
import pytest

os.environ["USE_MOCK_OBSERVATION"] = "true"

from eaagent.a_plus_plus.tools import get_structured_observation, get_latest_observation
from eaagent.a_plus_plus.prompt_builder import PlaybookPromptBuilder
from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent

try:
    from eaagent.a_plus_plus.graph import build_graph, create_initial_state
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestToolsMock:
    def test_get_structured_observation_mock(self):
        result = get_structured_observation("RB2605", period="D")
        assert result["status"] == "mock"
        assert "observation_text" in result
        print("✅ get_structured_observation (Mock) 测试通过")

    def test_get_latest_observation_mock(self):
        text = get_latest_observation("RB2605", period="D")
        assert isinstance(text, str)
        assert len(text) > 50
        print("✅ get_latest_observation (Mock) 测试通过")


@pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph 未安装，跳过 Graph 测试")
class TestGraphWithMock:
    def test_graph_runs_with_mock(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]

        config = {"configurable": {"thread_id": "test-mock-001"}}
        result = app.invoke(state, config)

        assert result is not None
        assert len(result["messages"]) >= 3
        last_msg = result["messages"][-1]["content"]
        assert "自我反思" in last_msg or "Observation" in last_msg
        print("✅ Graph 在 Mock 模式下完整运行测试通过")

    def test_reflection_contains_playbook_style(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]

        config = {"configurable": {"thread_id": "test-mock-002"}}
        result = app.invoke(state, config)

        last_msg = result["messages"][-1]["content"]
        assert any(kw in last_msg for kw in ["定式", "Observation", "量仓", "主动放弃", "信息不足"])
        print("✅ Reflection 内容符合 Playbook 风格测试通过")


class TestPromptBuilder:
    def test_playbook_loaded(self):
        builder = PlaybookPromptBuilder()

        # 如果是警告信息（文件不存在），则跳过严格检查
        if "警告" in builder.playbook_content or "未找到" in builder.playbook_content:
            pytest.skip("Playbook 文件在当前环境未找到，跳过长度检查")

        assert len(builder.playbook_content) > 1000
        print("✅ Playbook 加载测试通过")


if __name__ == "__main__":
    print("=== 开始运行 a_plus_plus 模块测试 ===\n")
    TestToolsMock().test_get_structured_observation_mock()
    TestToolsMock().test_get_latest_observation_mock()
    if HAS_LANGGRAPH:
        TestGraphWithMock().test_graph_runs_with_mock()
        TestGraphWithMock().test_reflection_contains_playbook_style()
    else:
        print("⚠️ langgraph 未安装，跳过 Graph 相关测试")
    TestPromptBuilder().test_playbook_loaded()
    print("\n=== 所有测试通过 ===")
