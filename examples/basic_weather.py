"""
eaagent 基础使用示例
运行前请设置环境变量：
    export XAI_API_KEY="xai-你的密钥"
"""

from eaagent import ReActAgent
from eaagent.tools import get_weather


def main():
    # 初始化 Agent
    agent = ReActAgent(
        model="grok-4.3",
        verbose=True,
        max_steps=10,
    )

    # 注册工具
    agent.add_tool(
        name="get_weather",
        description="查询指定城市的当前天气",
        parameters={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，支持中文或英文（如 北京 / Beijing）"
                }
            },
            "required": ["city"]
        },
        function=get_weather,
    )

    # 运行
    question = "北京今天天气怎么样？请帮我查一下。"
    print(f"\n问题: {question}\n")

    answer = agent.run(question)
    print(f"\n最终回复:\n{answer}")


if __name__ == "__main__":
    main()