from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors


def quality_sensor(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 质量检查 (Sensors)", Colors.WARNING)
    issues = []

    # ========== 1. 基础检查 ==========
    if len(state.get("observations", [])) < 2:
        issues.append("观察数据不足（当前仅1条结构化观察）")

    latest_signal = state.get("signals", [])[-1] if state.get("signals") else {}
    reason = latest_signal.get("reason", "")
    has_risk_control = any(kw in reason for kw in ["止损", "风险", "仓位", "轻仓"])

    if state.get("confidence", 1.0) < 0.75 and not has_risk_control:
        issues.append(f"置信度偏低（当前 {state.get('confidence', 0):.0%}），建议继续分析")

    # ========== 2. 前后轮信号一致性检查 ==========
    signals = state.get("signals", [])
    if len(signals) >= 2:
        prev_signal = signals[-2]
        curr_direction = latest_signal.get("direction", "")
        prev_direction = prev_signal.get("direction", "")

        if curr_direction and prev_direction and curr_direction != prev_direction:
            issues.append(f"信号方向变化（上一轮: {prev_direction} → 本轮: {curr_direction}），需验证")

    # ========== 3. 重要特征检测（加强版） ==========
    observations = state.get("observations", [])
    if observations:
        latest_obs = observations[-1]
        volume_oi_text = latest_obs.get("volume_oi_linkage", "").lower()
        force_text = latest_obs.get("force_comparison", "").lower()
        key_events = latest_obs.get("key_events", [])

        # 检测空头主动增仓 / 持仓大幅增加
        oi_increase_keywords = ["持仓增加", "持仓大幅增加", "oi大幅增加", "空头增仓", "持仓回升", "持仓持续增加"]
        if any(kw in volume_oi_text for kw in oi_increase_keywords):
            issues.append("检测到持仓量显著增加（空头主动增仓迹象），建议继续验证")

        # 检测关键破位
        break_keywords = ["破位", "跌破", "失守", "下破"]
        if any(kw in volume_oi_text for kw in break_keywords):
            issues.append("检测到关键价位破位，建议继续验证趋势有效性")

        # 辅助检测 force_comparison 中的空头主导信号
        if "空头力量占优" in force_text or "空头主导" in force_text:
            if "持仓增加" in volume_oi_text or "空头增仓" in volume_oi_text:
                issues.append("量仓共振显示空头持续增仓，建议继续验证")

    # ========== 4. 结构化输出 ==========
    state["issues"] = issues
    state["risk_assessment"] = {
        "issues_count": len(issues),
        "issues": issues,
        "has_signal_change": any("信号方向变化" in i for i in issues),
        "has_oi_increase": any("持仓量" in i or "空头增仓" in i for i in issues),
        "has_breakout": any("破位" in i for i in issues),
    }
    state["analysis_rounds"] = state.get("iteration", 0)

    # 给 llm_critique 的建议（确保始终有值）
    if issues:
        state["sensor_suggestion"] = {
            "should_continue": True,
            "reason": "存在以下问题，建议继续分析验证：" + "；".join(issues)
        }
        color_print(f" → 发现的问题: {issues}", Colors.FAIL)
    else:
        state["sensor_suggestion"] = {
            "should_continue": False,
            "reason": "本轮分析未发现明显问题，信号逻辑完整，可考虑收敛"
        }
        color_print(" → 未发现明显问题", Colors.OKGREEN)

    return state
