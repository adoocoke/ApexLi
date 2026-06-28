from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
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

    # 融合版：Fortress铁律 + 完整详细Prompt + 强制要求
    base_prompt = build_fortified_observation_prompt(state.get("current_playbook", "v3"))

    prompt = f"""{base_prompt}

以下是 {state['current_symbol']} 的完整日线数据（包含 oi 和 oi_chg）：

{data_str}

**强制要求（必须严格遵守）**：
1. 必须明确写出参考了 Playbook 的哪一条或哪几条具体规则（写完整标题）
2. 必须说明当前市场情况如何匹配该规则
3. data_requests 必须是字典列表，不能是字符串

请严格按以下JSON格式返回（不要有任何额外文字）：

{{
  "phase": "当前所处阶段",
  "trend": {{"mid_term": "...", "short_term": "..."}},
  "key_levels": {{"strong_resistance": [...], "strong_support": [...]}},
  "volume_oi_linkage": "...",
  "key_events": [...],
  "force_comparison": "...",
  "trading_bias": "...",
  "main_contradiction": "...",
  "playbook_references": ["规则标题1（匹配理由）", "规则标题2（匹配理由）"],
  "data_requests": [
    {{"data_type": "相关品种日线", "reason": "...", "priority": "high", "symbols": ["I2609.DCE", "J2609.DCE"]}},
    {{"data_type": "技术指标", "reason": "...", "priority": "high", "indicators": ["MA5", "MA13", "MA20"]}}
  ]
}}"""

    system_prompt = state.get("messages", [{}])[0].get("content", "")

    from eaagent.a_plus_plus.utils.llm import call_llm
    response = call_llm(prompt, system_prompt)

    try:
        obs_data = json.loads(response)
    except Exception:
        obs_data = {"phase": "解析失败", "playbook_references": [], "data_requests": []}

    state["observations"].append(obs_data)
    color_print(f" → 本轮引用 Playbook: {obs_data.get('playbook_references', [])}", Colors.OKBLUE)
    
    return state
