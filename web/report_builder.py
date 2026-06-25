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

    md = f"""## 📊 Analysis Summary

- **Symbol**: `{symbol}`
- **Data Source**: {data_source}
- **Total Rounds**: {rounds}

### Final Trading Signal
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

    # Per-Round Analysis
    md += "\n## 🔄 Per-Round Analysis\n"

    for i, obs in enumerate(observations):
        round_num = i + 1
        md += f"\n### Round {round_num}\n"

        # Playbook References
        playbook_refs = obs.get("playbook_references", [])
        if playbook_refs:
            md += "**📖 Playbook References**:\n"
            for ref in playbook_refs:
                md += f"- `{ref}`\n"
            md += "\n"

        # Observation (截断处理，避免过长导致格式混乱)
        obs_str = str(obs)
        if len(obs_str) > 2200:
            truncated = obs_str[:2200] + "\n...(truncated)"
        else:
            truncated = obs_str
        md += f"**Observation**:\n```json\n{truncated}\n```\n"

    # 最后一轮 Issues
    if issues:
        md += "\n### ⚠️ Issues (Latest Round)\n```json\n" + str(issues) + "\n```\n"

    # Sensor Suggestion
    if sensor_suggestion:
        md += "\n### 🔍 Sensor Suggestion\n```json\n" + str(sensor_suggestion) + "\n```\n"

    # LLM Critique
    if critique_result:
        md += "\n### 🧠 LLM Critique\n```json\n" + str(critique_result) + "\n```\n"

        if isinstance(critique_result, dict):
            if critique_result.get("comparison_summary"):
                md += f"\n**Comparison Summary**: {critique_result['comparison_summary']}\n"
            if critique_result.get("risk_change"):
                md += f"**Risk Change**: `{critique_result['risk_change']}`\n"

    return md
