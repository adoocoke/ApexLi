from eaagent.a_plus_plus.types import TAState
from eaagent.a_plus_plus.utils.console import color_print, Colors
import json

def final_output(state: TAState) -> TAState:
    color_print("\n" + "="*70, Colors.BOLD)
    color_print(f"【{state['current_symbol']} 技术分析报告】（共 {state['analysis_rounds']} 轮）", Colors.BOLD)
    color_print("="*70, Colors.BOLD)

    color_print(f"数据来源: {state['data_source'].upper()}", Colors.OKCYAN)
    color_print(f"Playbook 使用: {'是' if state['playbook_used'] else '否'}", Colors.OKCYAN)
    color_print(f"实际分析轮次: {state['analysis_rounds']}", Colors.OKCYAN)

    # 多轮分析路径总结
    color_print("\n多轮分析路径总结:", Colors.OKBLUE)
    for i, obs in enumerate(state.get("observations", []), 1):
        refs = obs.get("playbook_references", [])
        print(f"  第 {i} 轮: {len(refs)} 条规则引用 | 主要矛盾: {obs.get('main_contradiction', 'N/A')}")

    # 关键引用规则一览 (structured from Step 2 EA-002)
    color_print("\n关键引用规则一览:", Colors.OKGREEN)
    all_refs = []
    for obs in state.get("observations", []):
        for ref in obs.get("playbook_references", []):
            if isinstance(ref, dict):
                all_refs.append(f"{ref.get('rule', 'N/A')}: {ref.get('match_reason', '')}")
            else:
                all_refs.append(str(ref))
    for r in all_refs[:6]:  # limit for clarity
        print(f"  • {r}")

    if state["signals"]:
        last_signal = state["signals"][-1]
        color_print("\n最终交易信号:", Colors.OKGREEN)
        print(json.dumps(last_signal, ensure_ascii=False, indent=2))

    # 最终决策依据
    color_print("\n最终决策依据:", Colors.OKCYAN)
    print("  • 基于多轮结构化观察 + Playbook 严格匹配")
    print("  • 综合 Sensors/Critique 验证，无明显矛盾")
    if state.get("issues"):
        print("  • 剩余问题:", state["issues"])

    if state["issues"]:
        color_print("\n⚠️  最终问题:", Colors.FAIL)
        for issue in state["issues"]:
            print(f"  • {issue}")
    else:
        color_print("\n✅ 分析完成，未发现明显问题", Colors.OKGREEN)

    color_print("="*70, Colors.BOLD)
    return state