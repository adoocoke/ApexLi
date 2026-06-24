import os
import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state
from eaagent.a_plus_plus.llm_tracker import LLMTracker


def run_analysis(symbol: str, data_source: str, progress=gr.Progress()):
    tracker = LLMTracker()

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

    from eaagent.a_plus_plus.utils import llm as llm_module
    original_call_llm = llm_module.call_llm

    current_node = {"name": "unknown"}

    def recording_call_llm(prompt: str, system_prompt: str = "") -> str:
        response = original_call_llm(prompt, system_prompt)
        usage = None
        if isinstance(response, dict):
            usage = response.get("usage")
            response = response.get("content", str(response))
        tracker.record_call(current_node["name"], prompt, response, usage)
        return response

    llm_module.call_llm = recording_call_llm

    # Patch node functions to track rounds and node name
    from eaagent.a_plus_plus import graph as graph_module
    original_signal = graph_module.signal_generation
    original_critique = graph_module.llm_critique

    def patched_signal(state):
        tracker.start_new_round()
        current_node["name"] = "signal_generation"
        return original_signal(state)

    def patched_critique(state):
        current_node["name"] = "llm_critique"
        return original_critique(state)

    graph_module.signal_generation = patched_signal
    graph_module.llm_critique = patched_critique

    try:
        progress(0.3, desc="Running analysis graph...")

        app = build_graph()
        state = create_initial_state(symbol)
        config = {"configurable": {"thread_id": state["thread_id"]}}
        final_state = app.invoke(state, config)
    finally:
        llm_module.call_llm = original_call_llm
        graph_module.signal_generation = original_signal
        graph_module.llm_critique = original_critique

    progress(1.0, desc="Analysis complete!")

    # 构建结果
    rounds = final_state.get("analysis_rounds", 0)
    signals = final_state.get("signals", [])
    final_signal = signals[-1] if signals else {}
    playbook_used = final_state.get("playbook_used", False)
    playbook_id = final_state.get("playbook_id", "")

    total_usage = tracker.get_total_usage()

    result_md = f"""## 📊 Analysis Summary

- **Symbol**: `{symbol}`
- **Data Source**: {data_source}
- **Total Rounds**: {rounds}
- **Playbook Used**: {"✅ Yes" if playbook_used else "❌ No"}
- **Playbook ID**: `{playbook_id}`

### Token Usage Summary
- **Total Prompt Tokens**: {total_usage['total_prompt_tokens']:,}
- **Total Completion Tokens**: {total_usage['total_completion_tokens']:,}
- **Total Tokens**: {total_usage['total_tokens']:,}
- **Estimated Cost (grok-3)**: ${total_usage['estimated_cost_usd']:.6f}

### Final Trading Signal
```json
{final_signal}
```
"""

    # 按轮次展示 LLM 调用记录
    for r in range(1, tracker.current_round + 1):
        round_records = tracker.get_records_by_round(r)
        round_usage = {
            "prompt": sum(rec.prompt_tokens for rec in round_records),
            "completion": sum(rec.completion_tokens for rec in round_records),
            "total": sum(rec.total_tokens for rec in round_records),
        }
        round_cost = (round_usage["prompt"] / 1_000_000 * LLMTracker.PROMPT_PRICE_PER_M +
                      round_usage["completion"] / 1_000_000 * LLMTracker.COMPLETION_PRICE_PER_M)

        result_md += f"""
<details>
<summary><b>🔄 Round {r} Analysis</b> (Tokens: {round_usage['total']}, Cost: ${round_cost:.6f})</summary>
"""
        for rec in round_records:
            result_md += f"""
### {rec.node}
**Prompt:**
```markdown
{rec.prompt}
```

**Response:**
```json
{rec.response}
```
"""
        result_md += "</details>\n"

    return result_md


# ==================== Gradio 界面 ====================
with gr.Blocks(title="ApexLi - Trading Analysis", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 ApexLi - Trading Analysis (LangGraph)")

    with gr.Row():
        with gr.Column(scale=3):
            symbol_input = gr.Textbox(
                label="Symbol",
                value="RB2605.SHF",
                placeholder="e.g. RB2605.SHF 或 000001"
            )
        with gr.Column(scale=2):
            data_source = gr.Dropdown(
                choices=["Mock", "Tushare", "Akshare"],
                value="Mock",
                label="Data Source"
            )

    analyze_btn = gr.Button("Start Analysis", variant="primary", size="lg")
    result_output = gr.Markdown(label="Analysis Result")

    analyze_btn.click(
        fn=run_analysis,
        inputs=[symbol_input, data_source],
        outputs=[result_output]
    )

    gr.Examples(
        examples=[
            ["RB2605.SHF", "Mock"],
            ["000001", "Akshare"],
            ["I2409", "Mock"],
            ["600000", "Tushare"],
        ],
        inputs=[symbol_input, data_source],
        label="Quick Examples"
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)
