import os
import pandas as pd
import gradio as gr

from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart
from web.report_builder import build_analysis_report


def run_analysis(symbol: str, data_source: str, progress=gr.Progress()):
    # 设置数据源
    if data_source == "Mock":
        os.environ["USE_MOCK_OBSERVATION"] = "true"
        os.environ["DATA_PROVIDER"] = "mock"
    elif data_source == "Tushare":
        os.environ["USE_MOCK_OBSERVATION"] = "false"
        os.environ["DATA_PROVIDER"] = "tushare_futures"
    elif data_source == "Akshare":
        os.environ["USE_MOCK_OBSERVATION"] = "false"
        os.environ["DATA_PROVIDER"] = "akshare_stock"

    progress(0, desc="Initializing analysis...")

    progress(0.3, desc="Running analysis graph...")

    app = build_graph()
    state = create_initial_state(symbol)
    config = {"configurable": {"thread_id": state["thread_id"]}}
    final_state = app.invoke(state, config)

    progress(1.0, desc="Analysis complete!")

    # 使用独立模块生成报告
    result_md = build_analysis_report(final_state, symbol, data_source)

    # K线图
    chart = None
    try:
        tech_data = final_state.get("extra_data", {}).get("technical_indicators", [])
        if tech_data:
            df = pd.DataFrame(tech_data)
            if not df.empty and 'trade_date' in df.columns:
                chart = create_candlestick_chart(df, symbol)
    except Exception as e:
        print(f"[Chart Error] {e}")

    return result_md, chart


# ==================== Gradio 界面 ====================
with gr.Blocks(title="ApexLi - Trading Analysis", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 ApexLi - Trading Analysis (LangGraph)")

    with gr.Row():
        with gr.Column(scale=3):
            symbol_input = gr.Textbox(label="Symbol", value="RB2610.SHF")
        with gr.Column(scale=2):
            data_source = gr.Dropdown(choices=["Mock", "Tushare", "Akshare"], value="Mock", label="Data Source")

    analyze_btn = gr.Button("Start Analysis", variant="primary", size="lg")

    with gr.Row():
        result_output = gr.Markdown(label="Analysis Result")
        chart_output = gr.Plot(label="K线图")

    analyze_btn.click(
        fn=run_analysis,
        inputs=[symbol_input, data_source],
        outputs=[result_output, chart_output]
    )

    gr.Examples(
        examples=[["RB2610.SHF", "Mock"], ["000001", "Akshare"]],
        inputs=[symbol_input, data_source]
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
