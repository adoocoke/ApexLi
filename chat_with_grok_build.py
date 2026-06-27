import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)

# 这里放我们之前的完整上下文（我已经帮你整理好）
messages = [
    {
        "role": "system",
        "content": "你是一个专业、严谨的 AI Agent 架构师和代码理解专家。请基于用户提供的项目代码和需求，给出清晰、结构化的分析和建议。"
    },
    {
        "role": "user",
        "content": """我当前的项目是 /Users/admin/Development/ai/eaagent，这是一个基于 LangGraph + ReAct 的期货技术分析代理项目。

[感谢你之前的深入理解和总结。下面我针对你提出的关键问题进行澄清和回答：

1. 多时间框架协同逻辑
- 日线（1d）：判断趋势，要求至少有两个以上明显的高低点确认趋势方向。
- 30分钟：重点识别双底、双顶、2B反转、头肩顶、头肩底等经典形态。
- 3分钟：重点看双底、双顶，或者明显的回撤后反抽。
- 信号融合规则：当不同时间框架信号冲突时，**坚决不做单**（这是重要的风控纪律）。

2. 风险控制
- 采用**动态止损**。
- 单笔固定使用 **30% 仓位**。
- 整体风控要能体现在代理的决策过程中，而不仅仅是 playbook 描述。

3. Playbook 的执行方式
- 希望代理能够**逐条参考 playbook** 进行分析和决策，而不是泛泛引用。
- Playbook 应该在系统中真正发挥“规则引擎”的作用，而不仅仅是 Prompt 里的背景知识。

4. 当前最关注的痛点和方向
我目前最想提升和解决的方向有三个：
- **Playbook 遵循度**：代理是否真正严格按照 playbook 的规则逐条执行，而不是只做表面引用。
- **Harness 在系统中的作用**：如何更好地发挥 Martin Fowler Agent Harness（Guides、Sensors、Actor、Steering、Memory）的理念，让系统更可观测、更可控、更有自我评估能力。
- **Tool 工具的调用**：当前 Tool 的设计和调用是否合理，如何让代理更高效、准确地调用 Tushare 等工具，以及未来扩展更多可执行工具（例如风险计算工具、形态识别工具等）。

以上是我的核心诉求。基于你已经对项目代码的深入理解，请结合以上澄清内容，帮我思考接下来应该如何演进这个系统。

如果你认为理解已经足够清晰，可以直接进入 Plan Mode，给我一个结构化的升级计划。]

请基于以上所有信息，先确认你是否已经充分理解我的项目现状和目标。如果理解到位，请直接进入 Plan Mode，给我一个结构化、可执行的演进计划。"""
    }
]

response = client.chat.completions.create(
    model="grok-build-0.1",
    messages=messages,
    temperature=0.3,
    max_tokens=8000,
    stream=True
)

print("Grok Build 回复：\n")
for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)