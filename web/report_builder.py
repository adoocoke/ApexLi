from typing import Any, Dict


def build_analysis_report(
    final_state: Dict[str, Any],
    symbol: str,
    data_source: str
) -> str:
    """
    根据 final_state 构建结构化的分析报告 Markdown
    """
    rounds = final_state.get("analysis_rounds", 0)
    signals = final_state.get("signals", [])
    final_signal = signals[-1] if signals else {}
    extra_data = final_state.get("extra_data", {})
    observations = final_state.get("observations", [])
    issues = final_state.get("issues", [])
    critique_result = final_state.get("critique_result", {})
    sensor_suggestion = final_state.get("sensor_suggestion", {})

    md = f"""<div style="font-family: system-ui; background: #1a1a1a; padding: 15px; border-radius: 8px; color: #eee;">

**{symbol} 技术分析报告** (共 {rounds} 轮 | 数据源: {data_source})

**最终交易信号**
```json
{final_signal}
```
"""

    # Extra Data
    if extra_data:
        md += "\n### 📈 Extra Data\n"
        if extra_data.get("related_futures"):
            md += f"- **Related Futures**: {len(extra_data['related_futures'])} records\n"
        if extra_data.get("technical_indicators"):
            md += f"- **Technical Indicators**: {len(extra_data['technical_indicators'])} records\n"

    # Per-Round Analysis (cleaner Markdown for gr.Markdown)
    md += "\n**多轮分析路径**\n"

    for i, obs in enumerate(observations):
        round_num = i + 1
        md += f"\n**第 {round_num} 轮**\n"

        # Playbook References (structured, easy to read)
        playbook_refs = obs.get("playbook_references", [])
        if playbook_refs:
            md += "**关键规则引用**:\n"
            for ref in playbook_refs[:3]:  # limit for readability
                md += f"- {ref}\n"
            md += "\n"

        # Main observation summary (avoid huge JSON dump)
        main_contradiction = obs.get("main_contradiction", "N/A")
        md += f"**主要矛盾**: {main_contradiction}\n\n"

    # Issues, Sensor, Critique (clean bullet points)
    if issues:
        md += "\n**⚠️ 发现问题**:\n" + "\n".join([f"- {issue}" for issue in issues[:5]]) + "\n"

    if sensor_suggestion:
        md += f"\n**质量传感器建议**: {sensor_suggestion}\n"

    if critique_result and isinstance(critique_result, dict):
        md += "\n**LLM Critique**:\n"
        if critique_result.get("comparison_summary"):
            md += f"- **对比总结**: {critique_result['comparison_summary']}\n"
        if critique_result.get("risk_change"):
            md += f"- **风险变化**: {critique_result['risk_change']}\n"
        if critique_result.get("reason"):
            md += f"- **原因**: {critique_result['reason']}\n"

    md += "\n---\n*报告由EA Agent生成 | 基于多轮结构化观察 + Playbook*</div>"
    return md
