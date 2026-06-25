from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors


def quality_sensor(state: TAState) -> TAState:
    color_print(f"[第 {state['iteration']} 轮] 质量检查 (Sensors)", Colors.WARNING)
    issues = []

    # 1. 基础检查（保留原有逻辑）
    if len(state["observations"]) < 2:
        issues.append("观察数据不足（当前仅1条结构化观察）")

    latest_signal = state["signals"][-1] if state["signals"] else {}
    reason = latest_signal.get("reason", "")
    has_risk_control = any(kw in reason for kw in ["止损", "风险", "仓位", "轻仓"])

    if state["confidence"] < 0.75 and not has_risk_control:
        issues.append(f"置信度偏低（当前 {state['confidence']:.0%}），建议继续分析")

    # 2. 新增：前后轮信号一致性检查
    if len(state["signals"]) >= 2:
        prev_signal = state["signals"][-2]
        curr_direction = latest_signal.get("direction", "")
        prev_direction = prev_signal.get("direction", "")

        if curr_direction and prev_direction and curr_direction != prev_direction:
            issues.append(f"信号方向变化（上一轮: {prev_direction} → 本轮: {curr_direction}），需验证")

    # 3. 新增：重要特征检测（基于最新 observation）
    if state["observations"]:
        latest_obs = state["observations"][-1]
        volume_oi = latest_obs.get("volume_oi_linkage", "")

        # 检测持仓量大幅增加（空头主动增仓）
        if any(keyword in volume_oi for keyword in ["持仓增加", "持仓大幅增加", "OI大幅增加", "空头增仓"]):
            issues.append("检测到持仓量显著增加（可能空头主动增仓），建议继续验证")

        # 检测关键破位
        if any(keyword in volume_oi for keyword in ["破位", "跌破", "失守"]):
            issues.append("检测到关键价位破位，建议继续验证趋势有效性")

    # 4. 结构化输出
    state["issues"] = issues
    state["risk_assessment"] = {
        "issues_count": len(issues),
        "issues": issues,
        "has_signal_change": any("信号方向变化" in i for i in issues),
        "has_oi_increase": any("持仓量" in i for i in issues),
    }
    state["analysis_rounds"] = state["iteration"]

    # 给 llm_critique 的建议
    if issues:
        state["sensor_suggestion"] = {
            "should_continue": True,
            "reason": "存在以下问题，建议继续分析验证：" + "；".join(issues)
        }
        color_print(f" → 发现的问题: {issues}", Colors.FAIL)
    else:
        state["sensor_suggestion"] = {
            "should_continue": False,
            "reason": "本轮分析未发现明显问题，信号逻辑完整"
        }
        color_print(" → 未发现明显问题", Colors.OKGREEN)

    return state
