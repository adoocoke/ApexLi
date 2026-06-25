import os
import pandas as pd
import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state

# ==================== K线图函数 ====================
def create_candlestick_chart(df: pd.DataFrame, symbol: str):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if df is None or df.empty:
        return None

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3]
    )

    # K线
    fig.add_trace(go.Candlestick(
        x=df['trade_date'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="K线"
    ), row=1, col=1)

    # 均线
    for ma_col, ma_name in [('ma_5', 'MA5'), ('ma_13', 'MA13'), ('ma_20', 'MA20')]:
        if ma_col in df.columns:
            fig.add_trace(go.Scatter(
                x=df['trade_date'],
                y=df[ma_col],
                name=ma_name,
                line=dict(width=1.5)
            ), row=1, col=1)

    # 成交量
    if 'vol' in df.columns:
        fig.add_trace(go.Bar(
            x=df['trade_date'],
            y=df['vol'],
            name="成交量",
            marker_color='rgba(100,100,100,0.5)'
        ), row=2, col=1)

    fig.update_layout(
        title=f"{symbol} K线图 + 均线",
        xaxis_rangeslider_visible=False,
        height=650,
        showlegend=True,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="成交量", row=2, col=1)

    return fig


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

    # ==================== 构建文字内容 ====================
    rounds = final_state.get("analysis_rounds", 0)
    signals = final_state.get("signals", [])
    final_signal = signals[-1] if signals else {}
    extra_data = final_state.get("extra_data", {})
    observations = final_state.get("observations", [])
    issues = final_state.get("issues", [])
    critique_result = final_state.get("critique_result", {})
    sensor_suggestion = final_state.get("sensor_suggestion", {})

    result_md = f"""## 📊 Analysis Summary

- **Symbol**: `{symbol}`
- **Data Source**: {data_source}
- **Total Rounds**: {rounds}

### Final Trading Signal
```json
{final_signal}
```
"""

    if extra_data:
        result_md += "\n### 📈 Extra Data\n"
        if extra_data.get("related_futures"):
            result_md += f"- **Related Futures**: {len(extra_data['related_futures'])} records\n"
        if extra_data.get("technical_indicators"):
            result_md += f"- **Technical Indicators**: {len(extra_data['technical_indicators'])} records\n"

    result_md += "\n## 🔄 Per-Round Analysis\n"

    for i, obs in enumerate(observations):
        round_num = i + 1
        result_md += f"\n### Round {round_num}\n"

        playbook_refs = obs.get("playbook_references", [])
        if playbook_refs:
            result_md += "**📖 Playbook References**:\n"
            for ref in playbook_refs:
                result_md += f"- `{ref}`\n"
            result_md += "\n"

        result_md += "**Observation**:\n```json\n"
        obs_str = str(obs)
        result_md += obs_str[:2200] + ("...\n(truncated)" if len(obs_str) > 2200 else "")
        result_md += "\n```\n"

    if issues:
        result_md += "\n### ⚠️ Issues (Latest Round)\n```json\n" + str(issues) + "\n```\n"

    if sensor_suggestion:
        result_md += "\n### 🔍 Sensor Suggestion\n```json\n" + str(sensor_suggestion) + "\n```\n"

    if critique_result:
        result_md += "\n### 🧠 LLM Critique\n```json\n" + str(critique_result) + "\n```\n"
        if isinstance(critique_result, dict):
            if critique_result.get("comparison_summary"):
                result_md += f"\n**Comparison Summary**: {critique_result['comparison_summary']}\n"
            if critique_result.get("risk_change"):
                result_md += f"**Risk Change**: `{critique_result['risk_change']}`\n"

    # ==================== K线图数据准备 ====================
    chart = None
    try:
        tech_data = extra_data.get("technical_indicators", [])
        if tech_data:
            df = pd.DataFrame(tech_data)
            if not df.empty and 'trade_date' in df.columns:
                df = df.sort_values('trade_date')
                chart = create_candlestick_chart(df, symbol)
    except Exception as e:
        print(f"[Chart] 生成K线图失败: {e}")

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
