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

    # 结构化prompt - 最小文字入侵，主要依赖Playbook (manager.load + build_prompt已包含输出要求/操作组/JSON Few-shot)
    fortress_prompt = build_fortified_observation_prompt(current_playbook)
    playbook_content, _ = manager.load_playbook(current_playbook)
    safe_playbook = str(playbook_content).replace("{", "{{").replace("}", "}}")

    prompt = f"""{fortress_prompt}

【当前 Playbook 完整内容（含输出要求、操作组纪律、JSON Few-shot）】
{safe_playbook}

以下是 {state['current_symbol']} 的日线数据（最近 {len(daily_data)} 根K线，**优先视觉图片分析**）：

{data_str}

【任务要求】：严格按Playbook第0节输出要求（日期+章节前缀+conf>=80+JSON only+无匹配观望+操作组）。先判断匹配规则。**工具调用优先** (visual_analyzer/holding/news/related if needed)。生成**所有**高置信signals（全历史趋势生命周期，视觉+Playbook匹配）。输出JSON。

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
    {{"rule": "规则标题1", "match_reason": "当前市场情况如何匹配这条规则的具体解释"}},
    {{"rule": "规则标题2", "match_reason": "当前市场情况如何匹配这条规则的具体解释"}}
  ],
  "data_requests": [
    {{"data_type": "相关品种日线", "reason": "分析当前主力合约需要其高度相关的品种数据（如RB需要I/JM）", "priority": "high", "symbols": ["相关合约1", "相关合约2"]}},
    {{"data_type": "longer_history", "reason": "5个月数据不足，需要12个月完整历史来生成高置信signal", "months": 12}}
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
    from eaagent.a_plus_plus.tools import visual_analyzer

    # Vision upgrade: 只在第一轮或有新data_requests时调用visual_analyzer (复用缓存图像, 避免重复生成/发送相同12mo PNG)
    is_first_round = len(state.get("observations", [])) == 0
    has_new_data_requests = bool(state.get("observations", [{}])[-1].get("data_requests", [])) if state.get("observations") else True
    force_new_image = is_first_round or has_new_data_requests

    visual_result = visual_analyzer(
        state.get("current_symbol", "RB2610.SHF"),
        months=12,
        force_new=force_new_image,
        playbook_name=state.get("current_playbook", "v3")
    )

    if visual_result.get("status") == "success" and visual_result.get("signals"):
        print(f"[Observation] Visual Analyzer 提供 {len(visual_result['signals'])} 个高置信signals (图像+Playbook)，优先使用 {'(新图像)' if force_new_image else '(缓存图像)'}")
        state["signals"] = visual_result["signals"]  # 直接注入state，供后续signal_generation/回测使用
        obs_data = {
            "phase": "视觉K线分析完成",
            "trading_bias": "基于Grok图像模式",
            "playbook_references": [{"rule": f"视觉+{state.get('current_playbook', 'v3')} Playbook综合", "match_reason": f"Grok vision分析完整K线图像，输出多买卖点 (严格引用{state.get('current_playbook', 'v3')}章节, 同一Playbook内买入/买平或卖出/卖平为一组操作)"}],
            "data_requests": [],
            "visual_signals": visual_result["signals"],
            "image_path": visual_result.get("image_path"),
            "is_cached_image": not force_new_image
        }
        # LLM prompt已强化: 数据充分时should_continue=false, 避免重复相同图像
    else:
        print("[Observation] Visual fallback to text LLM analysis")
        response = call_llm(prompt, system_prompt)
        try:
            if isinstance(response, str) and response.strip():
                obs_data = json.loads(response)
            else:
                obs_data = {"phase": "解析失败", "playbook_references": [], "data_requests": []}
        except Exception as e:
            print(f"[Observation] JSON parse error in fallback: {e}")
            obs_data = {"phase": "解析失败", "playbook_references": [], "data_requests": []}

    # Ensure structured playbook_references (Step 2 EA-002) + vision compatibility
    if isinstance(obs_data.get("playbook_references"), list):
        for i, ref in enumerate(obs_data["playbook_references"]):
            if isinstance(ref, str):
                if "：" in ref or ":" in ref:
                    parts = ref.split("：") if "：" in ref else ref.split(":")
                    obs_data["playbook_references"][i] = {
                        "rule": parts[0].strip(),
                        "match_reason": parts[1].strip() if len(parts) > 1 else ""
                    }
                else:
                    obs_data["playbook_references"][i] = {"rule": ref, "match_reason": ""}

    state["observations"].append(obs_data)
    color_print(f" → 本轮引用 Playbook: {obs_data.get('playbook_references', [])} | Visual signals: {len(obs_data.get('visual_signals', []))}", Colors.OKBLUE)

    return state
