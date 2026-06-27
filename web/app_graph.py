import os, sys, pandas as pd
from pathlib import Path
root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(root))

import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart
from eaagent.playbooks.manager import manager
from eaagent.tools.tushare_futures import get_futures_daily_with_ma

def run_analysis(symbol, data_source, playbook_name):
    os.environ["USE_MOCK_OBSERVATION"] = "false" if data_source == "Tushare" else "true"
    os.environ["DATA_PROVIDER"] = "tushare_futures"

    content, name = manager.load(playbook_name)

    app = build_graph()
    state = create_initial_state(symbol)
    final_state = app.invoke(state, {"configurable": {"thread_id": state["thread_id"]}})

    signal = final_state.get("signals", [{}])[-1]
    extra = final_state.get("extra_data", {})

    # 主合约K线
    df_main = pd.DataFrame(extra.get("technical_indicators", []))
    if df_main.empty:
        df_main = get_futures_daily_with_ma(symbol, months=3)
    main_chart = create_candlestick_chart(df_main, symbol)

    # 强制显示两个相关品种
    df_i = get_futures_daily_with_ma("I2609.DCE", months=2)
    df_j = get_futures_daily_with_ma("J2609.DCE", months=2)
    i_chart = create_candlestick_chart(df_i, "I2609.DCE (铁矿石)")
    j_chart = create_candlestick_chart(df_j, "J2609.DCE (焦炭)")

    result_text = f"✅ Playbook: {name} | 方向: {signal.get('direction', '观望')}"

    return result_text, main_chart, i_chart, j_chart

with gr.Blocks() as demo:
    gr.Markdown("# ApexLi • 主合约 & 相关品种K线（双图）")
    with gr.Row():
        symbol = gr.Textbox(value="RB2610.SHF", label="合约")
        source = gr.Dropdown(["Tushare", "Mock"], value="Tushare", label="数据源")
        playbook = gr.Dropdown(["v3", "zen", "dow", "abu"], value="v3", label="Playbook")
    btn = gr.Button("开始分析", variant="primary")

    with gr.Row():
        console = gr.Textbox(label="📜 分析过程", lines=10, scale=4)
        with gr.Column(scale=6):
            with gr.Tabs():
                with gr.Tab("当前合约 K线"):
                    main_plot = gr.Plot()
                with gr.Tab("相关品种 K线"):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**I2609.DCE**")
                            i_plot = gr.Plot()
                        with gr.Column():
                            gr.Markdown("**J2609.DCE**")
                            j_plot = gr.Plot()

    btn.click(
        fn=run_analysis,
        inputs=[symbol, source, playbook],
        outputs=[console, main_plot, i_plot, j_plot]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
