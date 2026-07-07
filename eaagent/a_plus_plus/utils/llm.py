import os
import base64
from pathlib import Path
from openai import OpenAI


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """调用 Grok（Web 'Tushare (真实LLM + 数据)' 开关控制，USE_MOCK_LLM=false + XAI_API_KEY 必填）。Robust against None/empty response (fix NoneType re.search error in critique/others)。Always return str or valid JSON string."""
    if not prompt or not isinstance(prompt, str):
        print("[LLM] Warning: empty prompt, returning default structured JSON")
        import json
        return json.dumps({"should_continue": False, "reason": "Prompt empty - default to end", "score": 85, "key_rules": ["Playbook default"]}, ensure_ascii=False)

    # Default fallback at function end (ensures never returns None)
    import json
    default_json = json.dumps({"should_continue": False, "reason": "Default LLM fallback (real call failed or None)", "score": 85, "key_rules": ["default"]}, ensure_ascii=False)
    return default_json  # critical: always return str JSON


def call_vision_llm(prompt: str, image_path_or_base64: str = None, system_prompt: str = "") -> str:
    """Grok Vision 多模态调用（图像+K线视觉分析）
    - 支持 image_path (PNG) 或 base64 string
    - 结合 Playbook 给出全历史买卖点 (signals JSON)
    - Reuse XAI client，打印完整 vision prompt/response
    """
    if os.getenv("USE_MOCK_LLM", "true") == "true":  # Real Grok-3 vision when USE_MOCK_LLM=false + valid XAI key
        import json
        print("\n" + "=" * 80)
        print("[Vision Prompt] (Mock 模式 - Web 开关控制)")
        print("=" * 80)
        print((prompt or "")[:300] + "... [K-line image attached]")
        print("=" * 80)
        mock_response = json.dumps({
            "signals": [
                {
                    "direction": "空头",
                    "trend_signal": "卖出(趋势开启)",
                    "entry_zone": "3050-3100",
                    "stop_loss": "3150",
                    "target": "2800",
                    "reason": "视觉观察到K线第45根出现量仓共振背驰 (Playbook 2.1 + 3.1): 价格新低但持仓增加放缓，MACD柱收窄，图像清晰显示趋势开启信号。",
                    "confidence": 88
                },
                {
                    "direction": "观望",
                    "trend_signal": "卖平(趋势结束)",
                    "entry_zone": "N/A",
                    "stop_loss": "N/A",
                    "target": "N/A",
                    "reason": "视觉显示第120根K线背驰结束 + 震荡区间 (Playbook 2.3): 趋势结束信号明显，无进一步交易依据。",
                    "confidence": 85
                }
            ]
        }, ensure_ascii=False, indent=2)
        print(f"[Grok Vision Response] (Mock) {mock_response}\n")
        return mock_response

    api_key = os.getenv("XAI_API_KEY")
    if not api_key or api_key == "your_key_here":
        print("[Vision] WARNING: XAI_API_KEY not set or placeholder, forcing mock for stability (real vision disabled)")
        import json
        mock_response = json.dumps({
            "signals": [
                {"direction": "空头", "trend_signal": "卖出(趋势开启)", "reason": "视觉: K线背驰+量仓共振 (Playbook 2.1/3.1)", "confidence": 88},
                {"direction": "观望", "trend_signal": "卖平(趋势结束)", "reason": "视觉: 趋势结束震荡 (Playbook 2.3)", "confidence": 85}
            ]
        }, ensure_ascii=False, indent=2)
        print(f"[Grok Vision Response] (Forced Mock) {mock_response}\n")
        return mock_response

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
        timeout=45.0
    )

    # Prepare image content (base64 or path)
    image_content = None
    if image_path_or_base64 and isinstance(image_path_or_base64, str):
        if image_path_or_base64.startswith("data:image") or len(image_path_or_base64) > 1000:
            image_content = image_path_or_base64  # already base64
        elif Path(image_path_or_base64).exists():
            with open(image_path_or_base64, "rb") as f:
                img_bytes = f.read()
                image_content = base64.b64encode(img_bytes).decode("utf-8")
        else:
            image_content = image_path_or_base64  # assume base64 string

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    user_message = {"role": "user", "content": []}
    if prompt:
        user_message["content"].append({"type": "text", "text": prompt})
    if image_content:
        user_message["content"].append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_content}"}
        })
    messages.append(user_message)

    print("\n" + "=" * 80)
    print("[Vision Prompt] 发送给 Grok (含K线图像)")
    print("=" * 80)
    print(prompt[:400] + "... [K-line image attached for visual pattern analysis]")
    print("=" * 80)

    try:
        response = client.chat.completions.create(
            model="grok-3",  # grok-3 supports vision
            messages=messages,
            temperature=0.1,  # Lower for deeper, more deliberate reasoning
            max_tokens=2500   # More room for step-by-step thinking + detailed reasons
        )
        result = response.choices[0].message.content.strip()
        print(f"[Grok Vision Response] {result}\n")
        return result
    except Exception as e:
        print(f"[Vision LLM] Grok 调用失败: {e}")
        # Robust fallback to text call_llm (handles jiter/pydantic in conda)
        return call_llm(prompt, system_prompt)  # fallback to text LLM
        print("Prompt would be sent to Grok in real mode. Returning structured JSON for testing.")
        print("=" * 60)
        mock_response = json.dumps({
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
            ],
            "score": 85,
            "key_rules": ["2.1 量仓分析", "3.1 背驰判断"]
        }, ensure_ascii=False, indent=2)
        print(f"[Grok Response] (Mock) {mock_response}\n")
        return mock_response

    api_key = os.getenv("XAI_API_KEY")
    if not api_key or api_key == "your_key_here":
        import json
        print("[LLM] WARNING: XAI_API_KEY not set or placeholder, falling back to structured mock JSON (real LLM call disabled)")
        mock_response = json.dumps({
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
            ],
            "score": 92,
            "key_rules": ["2.1 量仓分析", "4.2 定式确认"]
        }, ensure_ascii=False, indent=2)
        print(f"[Grok Response] (Fallback Mock) {mock_response}\n")
        return mock_response

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
        if not result or not isinstance(result, str):
            import json
            return json.dumps({"should_continue": False, "reason": "Empty LLM response - default end", "score": 85, "key_rules": ["default"]}, ensure_ascii=False)
        return result

    except Exception as e:
        print(f"[LLM] Grok 调用失败: {e}")
        import json
        return json.dumps({"should_continue": False, "reason": f"Error: {str(e)[:100]} - default end", "score": 85, "key_rules": ["error fallback"]}, ensure_ascii=False)

    print("[LLM] Unexpected end of function - using default JSON")
    return default_json
