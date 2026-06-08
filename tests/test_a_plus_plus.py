import os
import pytest

# 强制开启 Mock 模式进行测试
os.environ["USE_MOCK_OBSERVATION"] = "true"

from eaagent.a_plus_plus.tools import get_structured_observation, get_latest_observation
from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from eaagent.a_plus_plus.prompt_builder import PlaybookPromptBuilder
from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent


class TestToolsMock:
    """测试 Mock 模式下的工具"""

    def test_get_structured_observation_mock(self):
        result = get_structured_observation("RB2605", period="D")
        assert result["status"] == "mock"
        assert "observation_text" in result
        assert "最新收盘" in result["observation_text"]
        assert result["atr"] is not None
        assert result["ma20"] is not None
        print("✅ get_structured_observation (Mock) 测试通过")

    def test_get_latest_observation_mock(self):
        text = get_latest_observation("RB2605", period="D")
        assert isinstance(text, str)
        assert len(text) > 50
        print("✅ get_latest_observation (Mock) 测试通过")


class TestGraphWithMock:
    """测试在 Mock 模式下完整 Graph 流程"""

    def test_graph_runs_with_mock(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前螺纹钢走势"}]

        config = {"configurable": {"thread_id": "test-mock-001"}}
        result = app.invoke(state, config)

        assert result is not None
        assert len(result["messages"]) >= 3  # 至少有 user + assistant + system/reflection

        # 检查最后一条消息包含反思内容
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
        # 检查是否体现了 Playbook 风格（主动要求数据 / 强调定式等）
        assert any(keyword in last_msg for keyword in ["定式", "Observation", "量仓", "主动放弃", "信息不足"])
        print("✅ Reflection 内容符合 Playbook 风格测试通过")


class TestPromptBuilder:
    """测试 PromptBuilder"""

    def test_playbook_loaded(self):
        builder = PlaybookPromptBuilder()
        assert len(builder.playbook_content) > 1000
        assert "量仓" in builder.playbook_content or "Playbook" in builder.playbook_content
        print("✅ Playbook 加载测试通过")


if __name__ == "__main__":
    print("=== 开始运行 a_plus_plus 模块测试 ===\n")
    TestToolsMock().test_get_structured_observation_mock()
    TestToolsMock().test_get_latest_observation_mock()
    TestGraphWithMock().test_graph_runs_with_mock()
    TestGraphWithMock().test_reflection_contains_playbook_style()
    TestPromptBuilder().test_playbook_loaded()
    print("\n=== 所有测试通过 ===")
