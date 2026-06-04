"""
ReAct Agent - 基于 Grok (xAI) 的简洁 ReAct 实现
支持自定义工具、自动工具调用循环
"""

import os
import json
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class ReActAgent:
    """
    简洁强大的 ReAct Agent
    使用 Grok 模型 + 工具调用实现思考-行动循环
    """

    def __init__(
        self,
        model: str = "grok-4.3",
        api_key: Optional[str] = None,
        base_url: str = "https://api.x.ai/v1",
        temperature: float = 0.7,
        max_steps: int = 15,
        verbose: bool = True,
    ):
        """
        初始化 ReAct Agent

        Args:
            model: Grok 模型名称，推荐 grok-4.3
            api_key: xAI API Key，未提供则从环境变量 XAI_API_KEY 读取
            base_url: xAI API 地址
            temperature: 采样温度
            max_steps: 最大思考步数
            verbose: 是否打印详细执行过程
        """
        self.model = model
        self.temperature = temperature
        self.max_steps = max_steps
        self.verbose = verbose

        api_key = api_key or os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError("请提供 XAI_API_KEY 或设置环境变量 XAI_API_KEY")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.tools: List[Dict] = []
        self.tool_functions: Dict[str, Callable] = {}

    def add_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable,
    ):
        """
        添加自定义工具

        Args:
            name: 工具名称
            description: 工具描述（给模型看的）
            parameters: JSON Schema 参数定义
            function: 实际执行函数
        """
        tool_def = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self.tools.append(tool_def)
        self.tool_functions[name] = function

        if self.verbose:
            print(f"[Agent] 已注册工具: {name}")

    def _execute_tool(self, tool_call) -> str:
        """执行工具调用"""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")

        if name not in self.tool_functions:
            return f"错误：未知工具 {name}"

        try:
            result = self.tool_functions[name](**args)
            return str(result)
        except Exception as e:
            return f"工具执行出错: {str(e)}"

    def run(self, goal: str) -> str:
        """
        运行 ReAct 循环

        Args:
            goal: 用户目标/问题

        Returns:
            最终答案
        """
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
                ),
            },
            {"role": "user", "content": goal},
        ]

        for step in range(1, self.max_steps + 1):
            if self.verbose:
                print(f"\n=== Step {step} ===")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                temperature=self.temperature,
            )

            assistant_msg = response.choices[0].message
            messages.append(assistant_msg.model_dump())

            # 有工具调用
            if assistant_msg.tool_calls:
                if self.verbose:
                    print(f"调用工具: {[tc.function.name for tc in assistant_msg.tool_calls]}")

                for tool_call in assistant_msg.tool_calls:
                    result = self._execute_tool(tool_call)

                    if self.verbose:
                        print(f"工具返回: {result[:200]}{'...' if len(result) > 200 else ''}")

                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result,
                    }
                    messages.append(tool_message)
            else:
                # 没有工具调用 → 最终答案
                final_answer = assistant_msg.content or ""
                if self.verbose:
                    print(f"\n✅ 最终答案:\n{final_answer}")
                return final_answer

        return "已达到最大步数限制，未能得到最终答案。"

    def chat(self, goal: str) -> str:
        """run 的别名，方便使用"""
        return self.run(goal)