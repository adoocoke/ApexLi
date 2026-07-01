from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.playbooks import manager
from eaagent.prompts.fortress import build_fortified_observation_prompt
import json
import pandas as pd
from typing import List, Dict, Any

def _prepare_daily_data(daily_data: List[Dict[str, Any]], max_rows: int = 60) -> str:
    if not daily_data:
        return "【无可用历史数据】"
    df = pd.DataFrame(daily_data)
    keep_cols = ["trade_date", "open", "high", "low", "close", "vol", "amount", "oi", "oi_chg"]
    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols].tail(max_rows)
    return df.to_csv(index=False)

def structured_observation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 结构化市场观察", Colors.OKCYAN)

    daily_data = state.get("market_data", {}).get("daily_df", [])
    data_str = _prepare_daily_data(daily_data)

    current_playbook = state.get("current_playbook", "v3")

    # 获取 Fortress 铁律
    fortress_prompt = build_fortified_observation_prompt(current_playbook)

    # 【正确获取 Playbook 内容】
    playbook_content, _ = manager.load_playbook(current_playbook)

    prompt = f"""{fortress_prompt}

【当前 Playbook 完整内容】
{playbook_content}

以下是 {state['current_symbol']} 的日线数据（最近 {len(daily_data)} 根K线）：

{data_str}

【任务要求 - 必须严格遵守】

1. **必须先判断**当前行情是否真的匹配 Playbook 中的规则，再决定是否引用。
2. `playbook_references` 字段的每一项必须同时包含：
   - 规则完整标题
   - 当前市场情况如何匹配这条规则的具体解释（至少一句话）
3. **工具调用优先**：如果需要额外期货数据（如持仓排名、相关合约主力、结算价、K线），**必须先调用工具** (get_futures_holding, get_futures_basic, get_related_futures_dynamic, generate_kline_chart)。可用工具已注册 (15000积分覆盖, doc_id=290 fut_holding)。调用格式为 tool call tool_name with 。如果工具缺失，输出 "NEED_TOOL: tool_name (reason)"。

4. 输出必须严格遵守以下 JSON 格式（不要有多余文字）：

{{
  "phase": "当前所处阶段描述",
  "trend": {{"mid_term": "上升/下降/震荡", "short_term": "上升/下降/震荡"}},
  "key_levels": {{"strong_resistance": [...], "strong_support": [...]}},
  "volume_oi_linkage": "量仓关系分析",
  "key_events": ["关键事件1", "关键事件2"],
  "force_comparison": "多空力量对比",
  "trading_bias": "偏多/偏空/观望",
  "main_contradiction": "当前最主要矛盾",
  "playbook_references": [
    "规则标题1：当前市场情况如何匹配这条规则的解释",
    "规则标题2：当前市场情况如何匹配这条规则的解释"
  ],
  "data_requests": [
    {{"data_type": "相关品种日线", "reason": "分析{state['current_symbol']}需要其高度相关的品种数据（如RB需要I/JM）", "priority": "high", "symbols": ["相关合约1", "相关合约2"]}}
  ]
}}

【Few-shot 示例】

示例1：
当价格持续回落 + 持仓稳步增加时，合理的引用写法：
"2.1 量仓分析核心逻辑：价格回落同时持仓稳步增加，符合持仓增加提供趋势燃料的规则，当前空头力量占优。"

示例2：
当价格新高但MACD柱子明显缩短时，合理的引用写法：
"3.1 背驰判断标准：价格虽然创新高，但MACD柱子面积小于前一段，出现趋势背驰，符合一卖信号特征。"

请严格按照以上要求输出 JSON。
"""

    system_prompt = state.get("messages", [{}])[0].get("content", "") if state.get("messages") else ""

    from eaagent.a_plus_plus.utils.llm import call_llm
    response = call_llm(prompt, system_prompt)

    try:
        obs_data = json.loads(response)
    except Exception:
        obs_data = {"phase": "解析失败", "playbook_references": [], "data_requests": []}

    state["observations"].append(obs_data)
    color_print(f" → 本轮引用 Playbook: {obs_data.get('playbook_references', [])}", Colors.OKBLUE)

    return state
