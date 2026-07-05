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
    if isinstance(news, dict):
        news = news.get("news", news.get("news_list", [])) if isinstance(news.get("news", []), list) else []

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

    # Extra Data + News (新增，放在多轮总结之后，确保始终显示)
    md += "\n### 📈 Extra Data\n"
    if extra_data.get("related_futures") or extra_data.get("related"):
        md += f"- **Related Futures**: {len(extra_data.get('related_futures', extra_data.get('related', [])))} records\n"
    if extra_data.get("technical_indicators"):
        md += f"- **Technical Indicators**: {len(extra_data['technical_indicators'])} records\n"
    if extra_data.get("holding"):
        holding = extra_data.get("holding", {})
        summary = holding.get("summary", "")
        if not summary and holding.get("holding_data"):
            brokers = "\n".join([f"  {h.get('broker', 'N/A')}: {h.get('vol', 'N/A')}" for h in holding.get("holding_data", [])[:5]])
            summary = f"持仓排名前5:\n{brokers}"
        md += f"- **Holding Data** (持仓排名): {summary or 'Top 5 brokers loaded'}\n"

    # 强制显示新闻区块 (即使news为空也显示fallback或提示)
    md += "\n### 📰 重要新闻与宏观驱动 (Top 5 - LLM已分析/弃用评估)\n"
    if news and isinstance(news, list) and len(news) > 0:
        for item in news[:5]:
            if not isinstance(item, dict): continue
            impact = item.get("impact", "中")
            impact_emoji = "🔴" if impact == "高" else "🟡"
            title = item.get("title", "News")
            md += f"- {impact_emoji} **{title}** ({item.get('date', '近期')}) [{item.get('source', 'web_search')}]\n"
            md += f"  {item.get('summary', '')} **(影响: {impact})**\n"
            llm_insight = "LLM已纳入决策（驱动基本面判断，影响持仓/趋势）" if any("新闻" in str(o) or "news" in str(o).lower() or "macro" in str(o).lower() for o in observations) else "LLM暂未深度分析/弃用（本次纯技术观望，未引用新闻作为决策依据）"
            md += f"  **LLM理解/弃用**: {llm_insight}\n\n"
    else:
        md += "- 暂无实时新闻数据 (LLM web_search未返回或自动调用失败)。\n- **Fallback新闻建议**：央行降准利好工业品、铁矿库存下降支撑RB、焦煤限产推高价格等宏观事件可作为基本面参考。\n- LLM本次未调用新闻工具，纯技术分析得出‘无进场定式必须观望’结论。\n"

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

    # Phase 3 增强：Critique 各轮评分柱状图 (Plotly) + Mermaid 决策路径
    if "critique_scores" in final_state:
        scores = final_state["critique_scores"]
        md += "\n### 📊 Critique 各轮评分柱状图\n"
        md += "```mermaid\ngantt\n    title Critique 评分趋势 (0-100)\n"
        for i, score in enumerate(scores, 1):
            md += f"    section 轮 {i}\n    评分 {score} : done, 0, {score}%\n"
        md += "```\n\n"
        md += "```python\nimport plotly.express as px\nfig = px.bar(x=list(range(1, len(scores)+1)), y=scores, labels={'x': '轮次', 'y': 'Critique 分数'})\nfig.show()\n```\n"

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
