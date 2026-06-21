 """
ReAct Agent - 基于 Grok (xAI) 的完整实现
包含 Memory + 自动记忆 + 多方式安全读取 API Key（A计划）
"""

import os
import json
from typing import List, Dict, Any, Optional, Callable
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 尝试导入 keyring（本地安全存储）
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


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
        auto_memory: bool = False,
    ):
        self.model = model
        self.temperature = temperature
        self.max_steps = max_steps
        self.verbose = verbose
        self.auto_memory = auto_memory

        if require_api_key:
            final_key = self._get_api_key(api_key)
            if not final_key:
                raise ValueError(
                    "未找到 XAI_API_KEY！\n"
                    "本地推荐使用 keyring，CI 请在 GitHub Secrets 设置 XAI_API_KEY"
                )
            self.client = OpenAI(api_key=final_key, base_url=base_url)
        else:
            self.client = None  # 测试模式

        self.tools: List[Dict] = []
        self.tool_functions: Dict[str, Callable] = {}
        self.memory: Dict[str, str] = {}

    def _get_api_key(self, provided_key: Optional[str] = None) -> Optional[str]:
        """多优先级读取 API Key"""
        if provided_key:
            return provided_key

        # 环境变量（支持 GitHub CI）
        key = os.getenv("XAI_API_KEY")
        if key:
            if os.getenv("GITHUB_ACTIONS"):
                print("[CI] 从 GitHub Secrets 读取 XAI_API_KEY")
            return key

        # 系统密钥管理器（本地推荐）
        if HAS_KEYRING:
            try:
                key = keyring.get_password("eaagent", "xai_api_key")
                if key:
                    if self.verbose:
                        print("[Keyring] 从系统密钥管理器读取 XAI_API_KEY")
                    return key
            except Exception:
                pass

        return None

    def add_tool(self, name: str, description: str, parameters: Dict, function: Callable):
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

    def remember(self, key: str, value: str):
        """记住重要事实"""
        self.memory[key] = value
        if self.verbose:
            print(f"[Memory] 已记住: {key} = {value}")

    def recall(self, key: str = None):
        """取出记忆"""
        if key:
            return self.memory.get(key, "")
        return self.memory.copy()

    def _extract_and_store_memory(self, goal: str, final_answer: str):
        """自动提取关键事实并存入记忆"""
        if not self.client or not self.auto_memory:
            return

        prompt = f"""请从以下对话中提取1-3条最重要的关键事实，用简洁的 key: value 格式输出：

用户问题: {goal}
最终答案: {final_answer}

只输出事实，不要解释。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            text = response.choices[0].message.content or ""

            for line in text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    self.remember(k.strip(), v.strip())

            if self.verbose and any(self.memory):
                print(f"[Auto Memory] 已自动提取 {len(self.memory)} 条记忆")

        except Exception as e:
            if self.verbose:
                print(f"[Auto Memory] 提取失败: {e}")

    def _execute_tool(self, tool_call):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")
        if name not in self.tool_functions:
            return f"错误：未知工具 {name}"
        try:
            return str(self.tool_functions[name](**args))
        except Exception as e:
            return f"工具执行出错: {str(e)}"

    def run(self, goal: str) -> str:
        # 注入记忆到 System Prompt
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
                    "请严格遵循 ReAct 格式：Thought → Action → Observation → Answer。\n"
                    "只有信息足够时才给出最终答案。"
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
                if self.verbose:
                    print(f"调用工具: {[tc.function.name for tc in assistant_msg.tool_calls]}")

                for tool_call in assistant_msg.tool_calls:
                    result = self._execute_tool(tool_call)
                    if self.verbose:
                        print(f"工具返回: {result[:200]}...")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result,
                    })
            else:
                final_answer = assistant_msg.content or ""

                # 自动记忆提取
                if self.auto_memory:
                    self._extract_and_store_memory(goal, final_answer)

                if self.verbose:
                    print(f"\n✅ 最终答案:\n{final_answer}")
                return final_answer

        return "达到最大步数限制"

    def chat(self, goal: str) -> str:
        return self.run(goal)
