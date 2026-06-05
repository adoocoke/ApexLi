"""
ReAct Agent - 基于 Grok (xAI) 的简洁 ReAct 实现
支持自定义工具、自动工具调用循环 + 简单记忆（A计划）
"""

import os
import json
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ReActAgent:
    def __init__(
        self,
        model: str = "grok-4.3",
        api_key: Optional[str] = None,
        base_url: str = "https://api.x.ai/v1",
        temperature: float = 0.7,
        max_steps: int = 15,
        verbose: bool = True,
        require_api_key: bool = True,
    ):
        self.model = model
        self.temperature = temperature
        self.max_steps = max_steps
        self.verbose = verbose

        if require_api_key:
            api_key = api_key or os.getenv("XAI_API_KEY")
            if not api_key:
                raise ValueError("请提供 XAI_API_KEY 或设置环境变量 XAI_API_KEY")
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = None

        self.tools: List[Dict] = []
        self.tool_functions: Dict[str, Callable] = {}
        self.memory: Dict[str, str] = {}

    def add_tool(self, name, description, parameters, function):
        tool_def = {
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters},
        }
        self.tools.append(tool_def)
        self.tool_functions[name] = function
        if self.verbose:
            print(f"[Agent] 已注册工具: {name}")

    def remember(self, key: str, value: str):
        self.memory[key] = value
        if self.verbose:
            print(f"[Memory] 已记住: {key} = {value}")

    def recall(self, key: str = None):
        if key:
            return self.memory.get(key, "")
        return self.memory.copy()

    def _execute_tool(self, tool_call):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")
        if name not in self.tool_functions:
            return f"错误：未知工具 {name}"
        try:
            return str(self.tool_functions[name](**args))
        except Exception as e:
            return f"工具执行出错: {str(e)}"

    def run(self, goal: str):
        memory_content = ""
        if self.memory:
            memory_content = "\n当前已知记忆：\n" + "\n".join(
                [f"- {k}: {v}" for k, v in self.memory.items()]
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个严谨的 ReAct 助手（powered by Grok）。\n"
                    "请严格遵循以下格式：\n"
                    "1. 先在思考中分析当前情况（Thought）\n"
                    "2. 如果需要信息，调用工具（Action）\n"
                    "3. 只有当信息足够时，直接给出最终答案（Answer）\n"
                    "不要在给出最终答案后继续调用工具。"
                    f"{memory_content}"
                ),
            },
            {"role": "user", "content": goal},
        ]

        for step in range(1, self.max_steps + 1):
            if self.verbose:
                print(f"\n=== Step {step} ===")

            if self.client is None:
                return "测试模式：未实际调用 API"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                temperature=self.temperature,
            )

            assistant_msg = response.choices[0].message
            messages.append(assistant_msg.model_dump())

            if assistant_msg.tool_calls:
                for tool_call in assistant_msg.tool_calls:
                    result = self._execute_tool(tool_call)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result,
                    })
            else:
                return assistant_msg.content or ""

        return "达到最大步数限制"

    def chat(self, goal: str):
        return self.run(goal)
