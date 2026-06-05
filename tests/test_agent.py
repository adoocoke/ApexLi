"""
eaagent 测试套件
使用 pytest + unittest.mock
"""

import pytest
from unittest.mock import MagicMock, patch

from eaagent import ReActAgent


def test_agent_initialization():
    """测试 Agent 能否正常初始化"""
    agent = ReActAgent(
        model="grok-4.3",
        api_key="xai-test-key",
        verbose=False,
    )
    assert agent.model == "grok-4.3"
    assert agent.verbose is False
    assert len(agent.tools) == 0


def test_add_tool():
    """测试工具注册功能"""
    agent = ReActAgent(api_key="xai-test-key", verbose=False)

    def dummy_weather(city: str) -> str:
        return f"{city}天气很好"

    agent.add_tool(
        name="get_weather",
        description="查询城市天气",
        parameters={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名称"}
            },
            "required": ["city"],
        },
        function=dummy_weather,
    )

    assert len(agent.tools) == 1
    assert "get_weather" in agent.tool_functions


@patch("eaagent.agent.OpenAI")
def test_run_with_tool_call(mock_openai):
    """
    测试 Agent 能够正确调用工具并返回最终答案
    使用 mock 避免真实调用 xAI API
    """
    # 准备 mock 的 OpenAI client
    mock_client = MagicMock()
    mock_openai.return_value = mock_client

    # 第一次返回：要求调用工具
    first_response = MagicMock()
    first_response.choices[0].message.content = None
    first_response.choices[0].message.tool_calls = [
        MagicMock(
            id="call_abc123",
            function=MagicMock(
                name="get_weather",
                arguments='{"city": "北京"}'
            )
        )
    ]
    first_response.choices[0].message.model_dump.return_value = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": "call_abc123", "function": {"name": "get_weather"}}]
    }

    # 第二次返回：给出最终答案
    second_response = MagicMock()
    second_response.choices[0].message.content = "北京今天天气晴朗，25°C。"
    second_response.choices[0].message.tool_calls = None
    second_response.choices[0].message.model_dump.return_value = {
        "role": "assistant",
        "content": "北京今天天气晴朗，25°C。",
        "tool_calls": None
    }

    mock_client.chat.completions.create.side_effect = [first_response, second_response]

    # 初始化 Agent 并注册工具
    agent = ReActAgent(api_key="xai-test-key", verbose=False)

    def get_weather(city: str) -> str:
        return f"【{city}天气】晴朗，25°C，空气质量优"

    agent.add_tool(
        name="get_weather",
        description="查询天气",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
        function=get_weather,
    )

    # 执行测试
    result = agent.run("北京今天天气怎么样？")

    assert "北京今天天气晴朗" in result
    assert mock_client.chat.completions.create.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])