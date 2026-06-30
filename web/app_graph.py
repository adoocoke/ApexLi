# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
from pathlib import Path
root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root))

import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart
from eaagent.playbooks.manager import manager
from eaagent.tools.tushare_futures import get_futures_daily_with_ma, get_main_contracts, get_popular_main_contracts

def run_analysis(symbol, data_source, playbook_name, strategy_name="full"):
    # 设置数据源
    os.environ["USE_MOCK_OBSERVATION"] = "false" if data_source == "Tushare" else "true"
    os.environ["DATA_PROVIDER"] = "tushare_futures"
    os.environ["PLAYBOOK_STRATEGY"] = strategy_name  # 新增 Strategy 支持

    # 关键：先加载用户选择的 Playbook，拿到正确的 name
    content, name = manager.load(playbook_name)
    print(f"[DEBUG] Web 传递的 Playbook: {playbook_name} → 实际使用: {name} | Strategy: {strategy_name}")

    # 把正确的 name 传给 create_initial_state
    state = create_initial_state(symbol, playbook_name=name)

    app = build_graph()
    final_state = app.invoke(state, {"configurable": {"thread_id": state["thread_id"]}})

    signal = final_state.get("signals", [{}])[-1]
    extra = final_state.get("extra_data", {})

    # K线图部分（保持不变）
    df_main = pd.DataFrame(extra.get("technical_indicators", []))
    if df_main.empty:
        df_main = get_futures_daily_with_ma(symbol, months=3)
    main_chart = create_candlestick_chart(df_main, symbol)

    # 强制显示两个相关品种
    df_i = get_futures_daily_with_ma("I2609.DCE", months=2)
    df_j = get_futures_daily_with_ma("J2609.DCE", months=2)
    i_chart = create_candlestick_chart(df_i, "I2609.DCE (铁矿石)")
    j_chart = create_candlestick_chart(df_j, "J2609.DCE (焦炭)")
    result_text = f"✅ 当前使用 Playbook: {name} | 方向: {signal.get('direction', '未返回方向')}"

    return result_text, main_chart, i_chart, j_chart

with gr.Blocks() as demo:
    gr.Markdown("# ApexLi • 期货主力合约菜单 + 动态 K线")

    with gr.Row():
        popular_menu = gr.Dropdown(
            choices=get_popular_main_contracts(),
            value="RB2610.SHF",
            label="热门主力合约",
            interactive=True
        )
        all_menu = gr.Dropdown(
            choices=[c["ts_code"] for c in get_main_contracts()],
            value="I2609.DCE",
            label="所有活跃合约",
            interactive=True
        )
        source = gr.Dropdown(["Tushare", "Mock"], value="Tushare", label="数据源")
        playbook = gr.Dropdown(["v3", "zen", "dow", "abu"], value="v3", label="Playbook风格")
        strategy = gr.Dropdown(["full", "core", "idonly"], value="full", label="Strategy策略 (Token优化)")

    btn = gr.Button("开始完整分析 (EA)", variant="primary")

    with gr.Row():
        console = gr.Textbox(label="📜 分析过程", lines=10, scale=4)
        with gr.Column(scale=6):
            with gr.Tabs():
                with gr.Tab("当前合约 K线"):
                    main_plot = gr.Plot()
                with gr.Tab("相关品种 K线"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**铁矿石 I2609**")
                            i_plot = gr.Plot()
                        with gr.Column():
                            gr.Markdown("**焦炭 J2609**")
                            j_plot = gr.Plot()

    # 菜单变更立即更新主 K线 (新功能)
    def update_kline(symbol):
        df = get_futures_daily_with_ma(symbol, months=3)
        chart = create_candlestick_chart(df, symbol)
        return chart

    popular_menu.change(fn=update_kline, inputs=popular_menu, outputs=main_plot)
    all_menu.change(fn=update_kline, inputs=all_menu, outputs=main_plot)

    btn.click(
        fn=run_analysis,
        inputs=[popular_menu, source, playbook, strategy],
        outputs=[console, main_plot, i_plot, j_plot]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
