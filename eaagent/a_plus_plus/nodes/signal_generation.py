import json
import re
from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
from eaagent.a_plus_plus.utils.llm import call_llm
from eaagent.playbooks.manager import manager

def signal_generation(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 生成交易信号（Grok 分析）", Colors.OKGREEN)

    obs = state["observations"][-1] if state["observations"] else {}
    cur_playbook = state.get("current_playbook", "v3")
    relevant_rules = manager.get_rules(cur_playbook)

    # 结构化prompt - 最小文字入侵，核心规则/输出要求/操作组纪律/Few-shot全部来自Playbook (manager.build_prompt)
    playbook_content = manager.build_prompt(cur_playbook, max_chars=3500)
    prompt = f"""你是一个严格遵守 **当前{cur_playbook} Playbook** 的期货交易决策者。**基于完整K线历史 (5-12个月) + 工具 + 视觉结果**，一次性分析整段K线，输出**所有**高置信买卖点（趋势全生命周期）。严格只使用当前{cur_playbook}章节，禁止混用。

**当前Playbook完整规则（含第0节输出要求、操作组纪律、JSON Few-shot）**：
{playbook_content}

基于以下观察（含visual_signals）：
{obs}

**任务**：按Playbook要求输出JSON。视觉/K线匹配规则才输出signal（含精确日期、引用前缀"引用{cur_playbook}-X.Y"、conf>=80）。无匹配只观望。有依据就标记买卖/平仓（操作组：买入/买平、卖出/卖平为一组，破规则必须平仓）。覆盖趋势开启到结束。

只输出JSON，无额外文字。

可用工具 (必须用 tool call 格式调用)：
- get_futures_holding(ts_code): 持仓排名 (强烈推荐用于主力分析)
- get_futures_basic(exchange): 合约基本信息和主力列表
- get_related_futures_dynamic(symbol): 动态相关品种数据 (RB→I/JM, SA→FG/SH)
- get_futures_news(symbol, limit=5): 重要新闻/宏观政策 (驱动基本面)
- generate_kline_chart(symbol): K线图

**工具使用理由**：
- **News/Holding**：捕捉政策、主力仓位变化（增仓=趋势燃料），避免纯技术分析。
- **Related/Basic**：验证联动 + 合约规格/流动性。
- 如果5个月数据不足，请求 "longer_history" (12个月)。

如果需要工具但未提供, 输出 "NEED_TOOL: tool_name (reason for analysis)"。

    【当前 Playbook】
    {manager.build_prompt(cur_playbook)}

    基于以下结构化市场观察（已包含完整5-12个月K线数据），请**一次性分析整段K线**，输出**所有高置信买卖点**（趋势开启、背驰、定式确认等位置）。有明确**当前{cur_playbook} Playbook**规则匹配就标记买卖点，无明确依据的区间才观望。

    {obs}

    【输出要求 - 必须严格遵守】

    1. **输出多个signal**：基于整段K线历史，找出**所有符合当前{cur_playbook} Playbook的买卖点**（而非只当前最后一根K线）。每个signal对应一个具体K线位置。

    2. `reason` 字段必须同时包含：
       - **明确出自当前Playbook的章节/规则编号**（**必须以“引用{cur_playbook}-X.Y”开头**, e.g. "引用v3-2.1量仓分析核心逻辑" 或 "引用zen-2.1趋势背驰", **严格禁止混用zen和v3概念**）。
       - **具体哪根K线**为什么匹配这条规则的具体逻辑解释（结合历史数据 + 工具结果 + 量仓/背驰/定式）。
       - **一个分析只能出自相同的Playbook**（当前Web选择的{cur_playbook}），所有signal的reason必须一致引用同一个Playbook章节。

    3. **基于 Playbook 的信号要求**（LLM 必须从**当前{cur_playbook} Playbook**规则中推导，而非硬编码或混用其他Playbook概念）：
       - **买入/买平是一组操作**：买入后如果破了规则（背驰结束、持仓不再增加、定式失效）→ 必须输出“买平”。
       - **卖出/卖平是一组操作**：卖出后如果破了规则 → 必须输出“卖平”。
       - **趋势/仓位 signal** (`trend_signal` / `position_action`)：基于**当前{cur_playbook} Playbook**趋势判断规则，判断**趋势开启到结束**的全生命周期：
         - 下跌趋势**开启**（量仓确认、形态成立）→ “卖出(趋势开启)/做空”。
         - 下跌趋势**结束/震荡**（背驰、持仓不再增加、定式失效）→ “卖平(趋势结束)/观望”。
         - 上涨趋势**开启**（量仓确认、形态成立）→ “买入(趋势开启)/做空”。
         - 上涨趋势**结束/震荡**（背驰、持仓不再增加、定式失效）→ “买平(趋势结束)/观望”。
       - **有依据就标记**：如果K线位置匹配**当前{cur_playbook} Playbook**任何规则，必须输出对应signal + 详细reason（含Playbook章节）；**只有完全无匹配时才输出观望**。
       - **止损**：买入止损，前一个k线的低点，卖出止损前一根k线的高点。
       - 所有 signal 必须**严格引用当前{cur_playbook}具体章节**（e.g. “引用v3-2.1量仓分析核心逻辑：...” 或 “引用zen-2.2背驰判断：...”），并结合完整K线历史 + 工具数据给出**明确逻辑**。**只有有明确Playbook规则匹配才输出signal**；**像index 5678这种无明确原因/规则匹配的绝不能输出为signal**，必须归为“观望” + reason说明“无Playbook依据”。**禁止在一次分析中混用zen和v3概念**。

    4. 输出必须严格按照以下 JSON 格式返回（不要有任何额外文字，输出**signal列表**，每个signal对应一个K线位置）：

    {{
      "signals": [
        {{
          "direction": "多头 / 空头 / 观望",
          "trend_signal": "卖出(趋势开启) / 卖平(趋势结束) /买入(趋势开启) / 买平(趋势结束) / 持仓 / 观望",
          "entry_zone": "入场区间描述（或无）",
          "stop_loss": "止损描述（或无）",
          "target": "目标 / 减仓区间（或无）",
          "reason": "引用了规则X（Playbook具体标题）：在第N根K线位置，价格... + 历史数据 + 工具结果匹配该规则的具体逻辑...（必须包含规则引用 + 具体K线位置）",
          "confidence": 85
        }},
        ... (更多signal)
      ]
    }}

    【Few-shot 示例】（基于完整K线一次性输出多个signal）

    示例1（多个买卖点）：
    {{
      "signals": [
        {{
          "direction": "空头",
          "trend_signal": "卖出(趋势开启)",
          "reason": "引用v3-2.1量仓分析核心逻辑（当前Playbook v3）：在第45根K线位置，价格持续回落同时持仓稳步增加，符合‘持仓增加提供趋势燃料’规则，holding工具确认主力增仓，因此在该位置给出卖出(趋势开启) signal。",
          "confidence": 88
        }},
        {{
          "direction": "观望",
          "trend_signal": "卖平(趋势结束)",
          "reason": "引用v3-2.3趋势判断与行情选择（当前Playbook v3）：在第120根K线位置，出现背驰 + 持仓不再放大，趋势进入结束/震荡阶段，符合‘趋势结束时主动卖平仓位’规则，因此给出卖平 signal (买入/买平或卖出/卖平为一组操作, 破规则后必须平仓; index 5678这类无明确规则匹配的必须观望, 绝不输出为signal)。",
          "confidence": 85
        }}
      ]
    }}

    请严格按照以上要求输出 JSON（**基于完整K线数据一次性输出所有买卖点**，有Playbook规则匹配就标记，无明确依据才观望）。
    """

    system_prompt = state["messages"][0]["content"] if state["messages"] else ""
    response = call_llm(prompt, system_prompt)

    print(f"[SignalGen] LLM response received (type: {type(response)}, len: {len(str(response)) if response else 0})")

    try:
        if not isinstance(response, str) or not response.strip():
            response = '{"signals": []}'  # safe default to prevent NoneType
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            signal_data = json.loads(json_match.group(0))
        else:
            signal_data = json.loads(response)
        # 确保趋势相关字段存在（兼容旧输出 + Playbook 推导）
        if isinstance(signal_data, dict):
            if "trend_signal" not in signal_data:
                signal_data["trend_signal"] = signal_data.get("direction", "观望")
            if "position_action" not in signal_data:
                signal_data["position_action"] = signal_data.get("trend_signal", signal_data.get("direction", "观望"))
    except Exception as e:  # Catch all (JSONDecodeError, TypeError for None, etc.)
        print(f"[SignalGen] JSON parse failed: {type(e).__name__}: {e}. Raw preview: {str(response)[:150] if response else 'None'}")
        signal_data = {
            "direction": "观望",
            "trend_signal": "观望",
            "position_action": "空仓(震荡)",
            "entry_zone": "解析失败",
            "stop_loss": "解析失败",
            "target": "解析失败",
            "reason": str(response) if response else "LLM returned None - using visual signals from observation",
            "confidence": 60
        }

    # If visual_signals already in state from observation, prefer them (Phase 3 vision upgrade)
    if not state.get("signals") and state.get("observations"):
        last_obs = state["observations"][-1]
        if last_obs.get("visual_signals"):
            print(f"[SignalGen] Using visual_signals from observation (4 signals)")
            state["signals"] = last_obs["visual_signals"]
            signal_data = last_obs["visual_signals"][0] if last_obs["visual_signals"] else signal_data

    state["signals"].append(signal_data)
    state["confidence"] = round(0.65 + (state["iteration"] * 0.08), 2)
    return state