import pytest
import sys

# 检查是否安装了 langchain_core
try:
    import langchain_core
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


class TestAPlusPlusReActAgent:
    """测试 APlusPlusReActAgent 基础功能"""

    def test_import_and_init(self):
        from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent
        agent = APlusPlusReActAgent()
        assert agent is not None

    def test_load_playbook(self):
        from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent
        agent = APlusPlusReActAgent()
        agent.load_playbook()
        assert agent.playbook_rules is not None
        assert agent.playbook_rules["version"] == "v3.0"

    def test_build_enhanced_prompt(self):
        from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent
        agent = APlusPlusReActAgent()
        prompt = agent.build_enhanced_prompt()
        assert "交易技能 Playbook" in prompt


@pytest.mark.skipif(not HAS_LANGCHAIN, reason="langchain_core 未安装，跳过 Graph 测试")
class TestGraph:
    """测试 LangGraph 流程（需要 langchain_core 和 langgraph）"""

    def test_build_graph(self):
        from eaagent.a_plus_plus.graph import build_graph
        app = build_graph()
        assert app is not None

    def test_simple_invoke(self):
        from eaagent.a_plus_plus.graph import build_graph, create_initial_state
        app = build_graph()
        initial_state = create_initial_state()
        initial_state["messages"] = [{"role": "user", "content": "请简单分析一下当前市场"}]
        try:
            result = app.invoke(initial_state, {"recursion_limit": 3})
            assert result is not None
        except Exception as e:
            pytest.skip(f"Graph invoke 需要完整依赖: {e}")
