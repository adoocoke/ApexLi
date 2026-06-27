import os
import pandas as pd
import gradio as gr
import sys
from pathlib import Path

# 修复路径问题
root = Path(__file__).parent.parent.resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart


def run_analysis(symbol: str, data_source: str, progress=gr.Progress()):
    os.environ["USE_MOCK_OBSERVATION"] = "false" if data_source == "Tushare" else "true"
    os.environ["DATA_PROVIDER"] = "tushare_futures" if data_source == "Tushare" else "mock"

    progress(0.4, desc="正在运行分析...")

    app = build_graph()
    state = create_initial_state(symbol)
    final_state = app.invoke(state, {"configurable": {"thread_id": state["thread_id"]}})

    signal = final_state.get("signals", [{}])[-1]
    extra = final_state.get("extra_data", {})

    md = f"""# ApexLi 分析结果 (稳定版)

**合约**： {symbol}  
**数据源**： {data_source}  
**轮次**： {final_state.get('analysis_rounds', 0)}

**最终信号**： **{signal.get('direction', '观望')}**  
**入场**： {signal.get('entry_zone', 'N/A')}  
**止损**： {signal.get('stop_loss', 'N/A')}  
**理由**： {signal.get('reason', '完成')[:280]}...
"""

    # K线图 - 加强 fallback
    chart = None
    try:
        df = pd.DataFrame(extra.get("technical_indicators", []))
        if df.empty:
            from eaagent.tools.tushare_futures import get_futures_daily_with_ma
            df = get_futures_daily_with_ma(symbol, months=3)
        if not df.empty:
            chart = create_candlestick_chart(df, symbol)
    except Exception as e:
        print(f"[Kline Fallback Error] {e}")

    return md, chart


with gr.Blocks(title="ApexLi") as demo:
    gr.Markdown("# ApexLi - 稳定测试版")

    with gr.Row():
        symbol = gr.Textbox(value="RB2610.SHF", label="合约")
        source = gr.Dropdown(["Tushare", "Mock"], value="Tushare", label="数据源")

    btn = gr.Button("开始分析", variant="primary", size="large")

    with gr.Row():
        text = gr.Markdown("点击按钮开始...")
        plot = gr.Plot(label="📈 K线图")

    btn.click(run_analysis, inputs=[symbol, source], outputs=[text, plot])

    gr.Examples([["RB2610.SHF", "Tushare"]], inputs=[symbol, source])

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)