import os
import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state

llm_interactions = []


def run_analysis(symbol: str, data_source: str, progress=gr.Progress()):
    global llm_interactions
    llm_interactions = []

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

    def recording_call_llm(prompt: str, system_prompt: str = "") -> str:
        response = original_call_llm(prompt, system_prompt)
        llm_interactions.append({
            "prompt": prompt,
            "response": response,
            "system_prompt": system_prompt
        })
        return response

    llm_module.call_llm = recording_call_llm

    progress(0.3, desc="Running analysis graph...")

    app = build_graph()
    state = create_initial_state(symbol)
    config = {"configurable": {"thread_id": state["thread_id"]}}
    final_state = app.invoke(state, config)

    progress(1.0, desc="Analysis complete!")
    llm_module.call_llm = original_call_llm

    # 构建结果
    rounds = final_state.get("analysis_rounds", 0)
    signals = final_state.get("signals", [])
    final_signal = signals[-1] if signals else {}
    playbook_used = final_state.get("playbook_used", False)
    playbook_id = final_state.get("playbook_id", "")

    result_md = f"""## 📊 Analysis Summary

- **Symbol**: `{symbol}`
- **Data Source**: {data_source}
- **Total Rounds**: {rounds}
- **Playbook Used**: {"✅ Yes" if playbook_used else "❌ No"}
- **Playbook ID**: `{playbook_id}`

### Final Trading Signal
```json
{final_signal}
```
"""

    # 使用 details 标签实现可折叠效果
    for i in range(0, len(llm_interactions), 2):
        round_num = (i // 2) + 1
        sig = llm_interactions[i] if i < len(llm_interactions) else {}
        crit = llm_interactions[i + 1] if i + 1 < len(llm_interactions) else {}

        result_md += f"""
<details>
<summary><b>🔄 Round {round_num} Analysis</b></summary>

### signal_generation
**Prompt:**
```markdown
{sig.get('prompt', 'N/A')}
```

**Response:**
```json
{sig.get('response', 'N/A')}
```

### llm_critique
**Prompt:**
```markdown
{crit.get('prompt', 'N/A')}
```

**Response:**
```json
{crit.get('response', 'N/A')}
```

</details>
"""

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
EOF