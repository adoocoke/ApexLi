import os
import sys
from pathlib import Path
import pandas as pd
import gradio as gr

# 自动修复 web 模块导入问题
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from web.charts.kline import create_candlestick_chart

# 尝试导入实时数据获取函数（用于 fallback）
try:
    from eaagent.tools.tushare_futures import get_futures_daily_with_ma
except ImportError:
    get_futures_daily_with_ma = None


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

    # 构建文字报告
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
        result_md += obs_str[:2000] + ("...\n(truncated)" if len(obs_str) > 2000 else "")
        result_md += "\n```\n"

    if issues:
        result_md += "\n### ⚠️ Issues (Latest Round)\n```json\n" + str(issues) + "\n```\n"

    if sensor_suggestion:
        result_md += "\n### 🔍 Sensor Suggestion\n```json\n" + str(sensor_suggestion) + "\n```\n"

    if critique_result:
        result_md += "\n### 🧠 LLM Critique\n```json\n" + str(critique_result) + "\n```\n"

    # ==================== K线图（带 fallback） ====================
    chart = None
    tech_data = extra_data.get("technical_indicators", [])

    if tech_data:
        try:
            df = pd.DataFrame(tech_data)
            chart = create_candlestick_chart(df, symbol)
        except Exception as e:
            print(f"[Chart] 使用 extra_data 绘图失败: {e}")
    else:
        print("[Chart] extra_data 中没有 technical_indicators 数据或为空，尝试实时获取...")

        # Fallback: 实时获取数据用于绘图
        if data_source == "Tushare" and get_futures_daily_with_ma is not None:
            try:
                df = get_futures_daily_with_ma(symbol, months=3, ma_periods=[5, 13, 20])
                if not df.empty:
                    chart = create_candlestick_chart(df, symbol)
                    print(f"[Chart] Fallback 成功获取 {len(df)} 条数据并绘图")
            except Exception as e:
                print(f"[Chart] Fallback 获取数据失败: {e}")
        else:
            print("[Chart] 无法进行 fallback（非 Tushare 或缺少函数）")

    return result_md, chart


with gr.Blocks(title="ApexLi - Trading Analysis") as demo:
    gr.Markdown("# 🚀 ApexLi - Trading Analysis (LangGraph)")

    with gr.Row():
        with gr.Column(scale=3):
            symbol_input = gr.Textbox(label="Symbol", value="RB2610.SHF")
        with gr.Column(scale=2):
            data_source = gr.Dropdown(choices=["Mock", "Tushare", "Akshare"], value="Mock", label="Data Source")

    analyze_btn = gr.Button("Start Analysis", variant="primary", size="lg")

    with gr.Row():
        result_output = gr.Markdown(label="Analysis Result")
        chart_output = gr.Plot(label="K线图 + 均线")

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
