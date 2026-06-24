import os
import gradio as gr
from eaagent.a_plus_plus.graph import build_graph, create_initial_state

# Global recorder for LLM interactions (per run)
llm_interactions = []


def run_analysis(symbol: str, data_source: str, progress=gr.Progress()):
    """Run the full LangGraph analysis and collect LLM interactions."""
    global llm_interactions
    llm_interactions = []

    # Set environment variables for data source
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

    app = build_graph()
    state = create_initial_state(symbol)

    # Monkey-patch call_llm to record interactions
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

    progress(0.2, desc="Running analysis graph...")

    config = {"configurable": {"thread_id": state["thread_id"]}}
    final_state = app.invoke(state, config)

    progress(1.0, desc="Analysis complete!")

    # Restore original function
    llm_module.call_llm = original_call_llm

    # Build result summary
    rounds = final_state.get("analysis_rounds", 0)
    signals = final_state.get("signals", [])
    final_signal = signals[-1] if signals else {}
    playbook_used = final_state.get("playbook_used", False)
    playbook_id = final_state.get("playbook_id", "")

    result_md = f"""## Analysis Summary

- **Symbol**: {symbol}
- **Data Source**: {data_source}
- **Total Rounds**: {rounds}
- **Playbook Used**: {"Yes" if playbook_used else "No"}
- **Playbook ID**: {playbook_id}

### Final Trading Signal
```json
{final_signal}
```
"""

    # Build per-round accordions
    accordions = []
    # Group interactions by round (simple heuristic: every 2 calls = one round)
    for i in range(0, len(llm_interactions), 2):
        round_num = (i // 2) + 1
        sig = llm_interactions[i] if i < len(llm_interactions) else {}
        crit = llm_interactions[i+1] if i+1 < len(llm_interactions) else {}

        content = f"""### signal_generation
**Prompt:**
```markdown
{sig.get('prompt', 'N/A')}
```

**Response:**
```markdown
{sig.get('response', 'N/A')}
```

### llm_critique
**Prompt:**
```markdown
{crit.get('prompt', 'N/A')}
```

**Response:**
```markdown
{crit.get('response', 'N/A')}
```
"""
        acc = gr.Accordion(label=f"Round {round_num} Analysis", open=(round_num >= max(1, rounds-1)))
        accordions.append((acc, content))

    return result_md, accordions


with gr.Blocks(title="EA Agent - Advanced Analysis", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# EA Agent - Trading Analysis (LangGraph)")

    with gr.Row():
        symbol_input = gr.Textbox(label="Symbol", value="RB2605.SHF", placeholder="e.g. RB2605.SHF or 000001")
        data_source = gr.Dropdown(
            choices=["Mock", "Tushare", "Akshare"],
            value="Mock",
            label="Data Source"
        )

    analyze_btn = gr.Button("Start Analysis", variant="primary")

    result_output = gr.Markdown(label="Analysis Result")
    round_accordions = gr.Column()

    def on_analyze(symbol, source):
        result_md, acc_list = run_analysis(symbol, source)
        # Create dynamic accordions
        components = []
        for acc, content in acc_list:
            with acc:
                gr.Markdown(content)
            components.append(acc)
        return result_md, gr.Column(components)

    analyze_btn.click(
        fn=on_analyze,
        inputs=[symbol_input, data_source],
        outputs=[result_output, round_accordions]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
