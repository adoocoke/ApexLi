"""
自动记忆功能测试（A计划）
"""

import pytest
from unittest.mock import patch, MagicMock
from eaagent import ReActAgent


def test_auto_memory_parameter():
    agent = ReActAgent(verbose=False, require_api_key=False, auto_memory=True)
    assert agent.auto_memory is True


def test_extract_and_store_memory_exists():
    agent = ReActAgent(verbose=False, require_api_key=False)
    assert hasattr(agent, '_extract_and_store_memory')


@patch('eaagent.agent.OpenAI')
def test_auto_memory_extraction_flow(mock_openai_class):
    """测试自动记忆提取流程"""
    # Mock OpenAI client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "铁矿石趋势: 目前处于下降通道\n支撑位: 3720附近"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    # 使用 require_api_key=True，让它正常创建 client
    agent = ReActAgent(
        verbose=False,
        require_api_key=True,
        auto_memory=True
    )

    # 执行提取
    agent._extract_and_store_memory(
        goal="铁矿石现在怎么样？",
        final_answer="铁矿石目前处于下降通道，建议关注3720支撑位。"
    )

    # 验证模型被调用了
    assert mock_client.chat.completions.create.called, "模型应该被调用来进行记忆提取"

    # 验证有记忆被存入
    memory = agent.recall()
    assert len(memory) > 0
