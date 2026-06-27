import os
import pandas as pd
import gradio as gr
import sys
from pathlib import Path

root = Path(__file__).parent.parent.resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart
from eaagent.tools.tushare_futures import get_futures_daily_with_ma


def run_analysis(symbol: str, data_source: str, progress=gr.Progress()):
    os.environ["USE_MOCK_OBSERVATION"] = "false" if data_source == "Tushare" else "true"
    os.environ["DATA_PROVIDER"] = "tushare_futures" if data_source == "Tushare" else "mock"

    console = ["🚀 **开始分析**", f"合约: {symbol} | 数据源: {data_source}"]

    progress(0.3, desc="运行中...")
    app = build_graph()
    state = create_initial_state(symbol)
    final_state = app.invoke(state, {"configurable": {"thread_id": state["thread_id"]}})

    console += ["✅ 数据获取完成", "✅ 结构化观察完成", "✅ 数据补充完成", "✅ 信号生成完成", "✅ 分析结束"]

    signal = final_state.get("signals", [{}])[-1]
    extra = final_state.get("extra_data", {})

    # 主 K线 + 相关品种 K线（加强 fallback）
    main_chart = related_chart = None
    try:
        df_main = pd.DataFrame(extra.get("technical_indicators", []))
        if df_main.empty:
            df_main = get_futures_daily_with_ma(symbol, months=3)
        main_chart = create_candlestick_chart(df_main, symbol)

        # 相关品种 K线（取第一个相关品种）
        related_list = extra.get("related_futures", [])
        if related_list:
            df_related = pd.DataFrame(related_list[:60])
            related_chart = create_candlestick_chart(df_related, "I2609.DCE (相关)")
        else:
            df_related = get_futures_daily_with_ma("I2609.DCE", months=2)
            related_chart = create_candlestick_chart(df_related, "I2609.DCE (相关)")
    except Exception as e:
        print(f"[Chart Error] {e}")

    md = f"""**最终结论**  
**方向**：**{signal.get('direction', '观望')}**  
**入场**：{signal.get('entry_zone', '待确认')}  
**止损**：{signal.get('stop_loss', 'N/A')}  
**理由**：{signal.get('reason', '')[:300]}..."""

    return "\n".join(console), md, main_chart, related_chart


with gr.Blocks(title="ApexLi • 实时分析终端") as demo:
    gr.Markdown("# **ApexLi** • 实时分析终端（左侧 Console + 右侧双 K线）")

    with gr.Row():
        symbol = gr.Textbox(value="RB2610.SHF", label="合约", scale=3)
        source = gr.Dropdown(["Tushare", "Mock"], value="Tushare", label="数据源", scale=1)
        btn = gr.Button("🚀 开始分析", variant="primary", scale=1)

    with gr.Row():
        with gr.Column(scale=4):
            console = gr.Textbox(label="📜 实时分析过程", lines=18, value="等待开始...", interactive=False)
            result = gr.Markdown(label="📌 最终结论")

        with gr.Column(scale=6):
            with gr.Tabs():
                with gr.Tab("当前合约 K线"):
                    main_plot = gr.Plot()
                with gr.Tab("相关品种 K线"):
                    related_plot = gr.Plot()

    btn.click(
        fn=run_analysis,
        inputs=[symbol, source],
        outputs=[console, result, main_plot, related_plot]
    )

    gr.Examples([["RB2610.SHF", "Tushare"]], [symbol, source])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)