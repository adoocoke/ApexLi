import os
import pytest

os.environ["USE_MOCK_OBSERVATION"] = "true"

from eaagent.a_plus_plus.tools import get_structured_observation
from eaagent.a_plus_plus.prompt_builder import PlaybookPromptBuilder

try:
    from eaagent.a_plus_plus.visualization import plot_kline_with_channel
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False

try:
    from eaagent.a_plus_plus.graph import build_graph, create_initial_state
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False


class TestToolsMock:
    def test_get_structured_observation_daily(self):
        result = get_structured_observation("RB2605", period="D")
        assert result["status"] == "mock"
        assert "key_levels" in result
        print("✅ 日线 Observation 测试通过")

    def test_get_structured_observation_30min(self):
        result = get_structured_observation("RB2605", period="30")
        assert result["status"] == "mock"
        print("✅ 30分钟 Observation 测试通过")


@pytest.mark.skipif(not HAS_VISUALIZATION, reason="matplotlib/mplfinance 未安装，跳过可视化测试")
class TestVisualization:
    def test_plot_kline_with_channel_up(self):
        path = plot_kline_with_channel("RB2605", period="D", trend="up")
        assert path.endswith(".png")
        assert os.path.exists(path)
        print(f"✅ 上升趋势通道K线图测试通过: {path}")

    def test_plot_kline_with_channel_down(self):
        path = plot_kline_with_channel("RB2605", period="D", trend="down")
        assert path.endswith(".png")
        assert os.path.exists(path)
        print(f"✅ 下降趋势通道K线图测试通过: {path}")


@pytest.mark.skipif(not HAS_LANGGRAPH, reason="langgraph 未安装，跳过 Graph 测试")
class TestMultiTimeframeGraph:
    def test_graph_multi_timeframe(self):
        app = build_graph()
        state = create_initial_state()
        state["current_symbol"] = "RB2605"
        state["messages"] = [{"role": "user", "content": "请分析当前蟢纹钢走势"}]
        config = {"configurable": {"thread_id": "test-mtf-001"}}
        result = app.invoke(state, config)
        assert result is not None
        print("✅ 多时间框 Graph 测试通过")


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
    if HAS_VISUALIZATION:
        TestVisualization().test_plot_kline_with_channel_up()
        TestVisualization().test_plot_kline_with_channel_down()
    if HAS_LANGGRAPH:
        TestMultiTimeframeGraph().test_graph_multi_timeframe()
    TestPromptBuilder().test_playbook_loaded()
    print("\n=== 测试完成 ===")