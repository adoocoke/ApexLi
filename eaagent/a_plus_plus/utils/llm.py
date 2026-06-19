import os
from openai import OpenAI


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """调用 Grok（测试模式下直接返回固定字符串，无额外开销）"""
    if os.getenv("USE_MOCK_LLM") == "true":
        import json
        return json.dumps({
            "direction": "多头",
            "entry_zone": "2960-2975（支撑区低吸）",
            "stop_loss": "2940以下",
            "target": "3000-3020（第一目标）",
            "reason": "根据历史数据分析，当前处于反弹阶段，建议在支撑位附近做多。"
        }, ensure_ascii=False)

    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        import json
        return json.dumps({
            "direction": "多头",
            "entry_zone": "2960-2975（支撑区低吸）",
            "stop_loss": "2940以下",
            "target": "3000-3020（第一目标）",
            "reason": "根据历史数据分析，当前处于反弹阶段，建议在支撑位附近做多。"
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
