"""
自动记忆功能测试（A计划）
"""

import pytest
from unittest.mock import patch, MagicMock
from eaagent import ReActAgent


def test_auto_memory_parameter():
    """测试 auto_memory 参数是否能正常传入"""
    agent = ReActAgent(verbose=False, require_api_key=False, auto_memory=True)
    assert agent.auto_memory is True

    agent2 = ReActAgent(verbose=False, require_api_key=False, auto_memory=False)
    assert agent2.auto_memory is False


def test_extract_and_store_memory_exists():
    """测试 _extract_and_store_memory 方法是否存在"""
    agent = ReActAgent(verbose=False, require_api_key=False)
    assert hasattr(agent, '_extract_and_store_memory')
    assert callable(getattr(agent, '_extract_and_store_memory'))


@patch('eaagent.agent.OpenAI')
def test_auto_memory_extraction_flow(mock_openai_class):
    """
    测试自动记忆提取流程（使用 mock 避免真实调用）
    """
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "铁矿石趋势: 目前处于下降通道\n支撑位: 3720附近"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai_class.return_value = mock_client

    agent = ReActAgent(
        verbose=False,
        require_api_key=True,
        auto_memory=True
    )

    agent._extract_and_store_memory(
        goal="铁矿石现在怎么样？",
        final_answer="铁矿石目前处于下降通道，建议关注 3720 支撑位。"
    )

    assert mock_client.chat.completions.create.called
    memory = agent.recall()
    assert len(memory) > 0 or "铁矿石趋势" in memory
