from typing import Any, Dict
import pandas as pd


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
    news = final_state.get("news") or extra_data.get("news", [])

    md = f"""<div style="font-family: system-ui, -apple-system, BlinkMacSystemFont; background: linear-gradient(145deg, #1a1a2e, #16213e); padding: 20px; border-radius: 12px; color: #e0f0ff; border: 1px solid #334455; max-width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">

**{symbol} 多轮期货分析报告** (共 {rounds} 轮 | 数据源: {data_source} | 强制多轮验证)

<div style="background: #0f1626; padding: 12px; border-radius: 8px; margin: 15px 0; font-size: 0.95em;">
**最终交易信号**  
```json
{final_signal}
```
</div>

### 📊 多轮分析路径总结
"""
    # Richer per-round with better styling
    for i, obs in enumerate(observations):
        round_num = i + 1
        md += f"""
**第 {round_num} 轮观察**  
"""
        playbook_refs = obs.get("playbook_references", [])
        if playbook_refs:
            md += "**📌 关键规则引用** (引用EA Playbook):\n"
            for ref in playbook_refs[:4]:
                md += f"- **{ref}**\n"
            md += "\n"

        main_contradiction = obs.get("main_contradiction", "N/A")
        md += f"**核心矛盾与洞察**: {main_contradiction}\n\n"

    # Extra Data + News (新增，放在多轮总结之后)
    if extra_data:
        md += "\n### 📈 Extra Data\n"
        if extra_data.get("related_futures") or extra_data.get("related"):
            md += f"- **Related Futures**: {len(extra_data.get('related_futures', extra_data.get('related', [])))} records\n"
        if extra_data.get("technical_indicators"):
            md += f"- **Technical Indicators**: {len(extra_data['technical_indicators'])} records\n"
        if extra_data.get("holding"):
            md += f"- **Holding Data**: {extra_data.get('holding', {}).get('total_brokers', 0)} brokers\n"

    if news:
        md += "\n### 📰 重要新闻与宏观驱动 (Top 5)\n"
        for item in news[:5]:
            impact = item.get("impact", "中")
            impact_emoji = "🔴" if impact == "高" else "🟡"
            md += f"- {impact_emoji} **{item.get('title', 'News')}** ({item.get('date', '近期')}) [{item.get('source', 'macro')}]\n"
            md += f"  {item.get('summary', '')} **(影响: {impact})**\n\n"

    # Enhanced sections with HTML for blog-like feel
    md += """<div style="background: #112233; padding: 15px; border-radius: 8px; margin-top: 20px;">

### ⚠️ 风险与问题
"""
    if issues:
        md += "\n".join([f"- {issue}" for issue in issues[:6]]) + "\n"
    else:
        md += "- 无明显风险，发现强信号\n"

    if sensor_suggestion:
        md += f"\n**质量传感器**: {sensor_suggestion}\n"

    md += "\n### 🤖 LLM Critique (多轮审查)\n"
    if critique_result and isinstance(critique_result, dict):
        if critique_result.get("comparison_summary"):
            md += f"- **轮次对比**: {critique_result.get('comparison_summary', '')}\n"
        if critique_result.get("risk_change"):
            md += f"- **风险变化**: {critique_result.get('risk_change', '')}\n"
        if critique_result.get("reason"):
            md += f"- **审查理由**: {critique_result.get('reason', '')}\n"
    else:
        md += "- 审查通过，继续多轮验证\n"

    md += f"""
### 📌 最终决策依据
- **多轮路径**: 强制完成 {rounds} 轮分析 (confidence threshold 强制多轮)
- **关键规则**: 引用Playbook核心规则，结构化匹配
- **数据支撑**: Tools调用 (news/holding/related/basic) + 动态K线 + 持仓/仓单验证
- **风险评估**: {len(issues)} 个问题已评估
- **新闻作用**: 宏观政策/库存事件驱动基本面判断
</div>

---
*EA Agent • 富文本Blog风格报告 | 宽度优化至Web 50% | 强制多轮 (MAX_ROUNDS=5) | 生成于 {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}*</div>
"""
    return md
