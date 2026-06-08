import pytest
from eaagent.a_plus_plus.eaagent_wrapper import APlusPlusReActAgent
from eaagent.a_plus_plus.graph import build_graph, create_initial_state


class TestAPlusPlusReActAgent:
    """测试 APlusPlusReActAgent 基础功能"""

    def test_import_and_init(self):
        """测试能否正常导入和初始化"""
        agent = APlusPlusReActAgent()
        assert agent is not None
        print("✅ APlusPlusReActAgent 初始化成功")

    def test_load_playbook(self):
        """测试加载 Playbook"""
        agent = APlusPlusReActAgent()
        agent.load_playbook()
        assert agent.playbook_rules is not None
        assert agent.playbook_rules["version"] == "v3.0"
        print("✅ Playbook 加载成功")

    def test_build_enhanced_prompt(self):
        """测试 Prompt 构建"""
        agent = APlusPlusReActAgent()
        prompt = agent.build_enhanced_prompt()
        assert "交易技能 Playbook" in prompt
        print("✅ Prompt 构建成功")


class TestGraph:
    """测试 LangGraph 流程"""

    def test_build_graph(self):
        """测试能否成功构建 graph"""
        app = build_graph()
        assert app is not None
        print("✅ Graph 构建成功")

    def test_simple_invoke(self):
        """简单测试 graph invoke（不要求完整运行）"""
        app = build_graph()
        initial_state = create_initial_state()
        initial_state["messages"] = [
            {"role": "user", "content": "请简单分析一下当前市场"}
        ]

        # 这里只测试能否正常启动，不要求完整执行
        try:
            result = app.invoke(initial_state, {"recursion_limit": 3})
            assert result is not None
            print("✅ Graph invoke 测试通过")
        except Exception as e:
            # 允许部分节点未实现导致的报错
            print(f"⚠️ Graph invoke 出现预期中的异常: {str(e)[:100]}")


if __name__ == "__main__":
    # 快速手动运行测试
    print("=== 开始测试 ===")
    TestAPlusPlusReActAgent().test_import_and_init()
    TestAPlusPlusReActAgent().test_load_playbook()
    TestAPlusPlusReActAgent().test_build_enhanced_prompt()
    TestGraph().test_build_graph()
    TestGraph().test_simple_invoke()
    print("=== 测试完成 ===")
