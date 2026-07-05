"""
Phase 3 Test-First: Streamlit Dashboard 布局测试 (streamlit_dashboard.py)
测试 3栏布局、Tabs (多轮轨迹/K线/报告/回测)、侧边栏选择、右栏 State/日志。
复用现有 report_builder + kline + graph。
"""

import pytest
from unittest.mock import patch, MagicMock

# TODO: 实现 streamlit_dashboard.py 后取消 skip
@pytest.mark.skip("Phase 3 Dashboard 实现后启用")
def test_streamlit_3_column_layout():
    """测试推荐 3栏布局"""
    # 模拟 Streamlit 组件
    with patch("streamlit.sidebar") as mock_sidebar, \
         patch("streamlit.tabs") as mock_tabs, \
         patch("streamlit.columns") as mock_columns:
        
        # 左侧栏
        mock_sidebar.selectbox.return_value = "螺纹钢 RB2610.SHF"
        mock_sidebar.selectbox.return_value = "full"
        mock_sidebar.button.return_value = True
        
        # 主 Tabs
        mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        
        # 右栏
        mock_columns.return_value = [MagicMock(), MagicMock()]
        
        # 模拟调用 dashboard 主函数
        # from streamlit_dashboard import main
        # main()
        
        assert mock_sidebar.selectbox.call_count >= 3  # 品种、策略、Playbook
        assert mock_tabs.call_count >= 1
        print("✅ Streamlit 3栏 Dashboard 布局测试通过 (骨架)")


@pytest.mark.skip("Phase 3 Dashboard 实现后启用")
def test_dashboard_reuses_existing_components():
    """测试复用 report_builder + kline + graph"""
    # 模拟导入
    try:
        from web.report_builder import build_analysis_report
        from web.charts.kline import create_candlestick_chart
        from eaagent.a_plus_plus.graph import build_graph
        assert build_analysis_report is not None
        assert create_candlestick_chart is not None
        assert build_graph is not None
        print("✅ 复用现有组件测试通过")
    except ImportError as e:
        pytest.fail(f"复用失败: {e}")


if __name__ == "__main__":
    test_streamlit_3_column_layout()
    test_dashboard_reuses_existing_components()
    print("=== Phase 3 Dashboard tests completed ===")
