import os
from openai import OpenAI


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """调用 Grok（测试模式下直接返回固定字符串，无额外开销）"""
    if os.getenv("USE_MOCK_LLM") == "true":
        import json
        # 返回完整的 observation JSON（匹配 structured_observation 期望），避免 playbook_references 为 str 导致 format 错误
        return json.dumps({
            "phase": "上升趋势中的回调阶段",
            "trend": {"mid_term": "上升", "short_term": "震荡"},
            "key_levels": {"strong_resistance": [3050], "strong_support": [2880]},
            "volume_oi_linkage": "持仓增加伴随价格回落，空头力量占优",
            "key_events": ["主力增仓", "MACD背驰信号"],
            "force_comparison": "空头略占优",
            "trading_bias": "观望",
            "main_contradiction": "价格新低但持仓未明显放大",
            "playbook_references": [
                {"rule": "2.1 量仓分析核心逻辑", "match_reason": "价格回落同时持仓稳步增加，符合持仓增加提供趋势燃料的规则，当前空头力量占优"},
                {"rule": "3.1 背驰判断标准", "match_reason": "价格创新低但MACD柱子面积缩小，出现趋势背驰，符合一卖信号特征"}
            ],
            "data_requests": [
                {"data_type": "持仓排名", "reason": "判断主力博弈方向", "priority": "high"}
            ]
        }, ensure_ascii=False)

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        import json
        # 同上，返回完整 observation JSON（fallback 情况）
        return json.dumps({
            "phase": "上升趋势中的回调阶段",
            "trend": {"mid_term": "上升", "short_term": "震荡"},
            "key_levels": {"strong_resistance": [3050], "strong_support": [2880]},
            "volume_oi_linkage": "持仓增加伴随价格回落，空头力量占优",
            "key_events": ["主力增仓", "MACD背驰信号"],
            "force_comparison": "空头略占优",
            "trading_bias": "观望",
            "main_contradiction": "价格新低但持仓未明显放大",
            "playbook_references": [
                {"rule": "2.1 量仓分析核心逻辑", "match_reason": "价格回落同时持仓稳步增加，符合持仓增加提供趋势燃料的规则，当前空头力量占优"},
                {"rule": "3.1 背驰判断标准", "match_reason": "价格创新低但MACD柱子面积缩小，出现趋势背驰，符合一卖信号特征"}
            ],
            "data_requests": [
                {"data_type": "持仓排名", "reason": "判断主力博弈方向", "priority": "high"}
            ]
        }, ensure_ascii=False)

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
        timeout=30.0
    )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    print("\n" + "=" * 60)
    print("[LLM Prompt] 发送给 Grok")
    print("=" * 60)

    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=messages,
            temperature=0.3,
            max_tokens=1200
        )
        result = response.choices[0].message.content.strip()
        print(f"[Grok Response] {result}\n")
        return result

    except Exception as e:
        print(f"[LLM] Grok 调用失败: {e}")
        return "模型调用失败或超时，返回模拟结果。"
