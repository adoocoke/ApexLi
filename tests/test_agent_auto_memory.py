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
    # 1. 创建 mock 的 client 实例
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "铁矿石趋势: 目前处于下降通道"
    mock_client_instance.chat.completions.create.return_value = mock_response

    # 2. 当 ReActAgent 内部 new OpenAI() 时，返回我们的 mock 实例
    mock_openai_class.return_value = mock_client_instance

    # 3. 这里必须用 require_api_key=True（让它正常初始化 client）
    agent = ReActAgent(
        verbose=False,
        require_api_key=False,
        auto_memory=True
    )

    # 4. 调用提取方法
    agent._extract_and_store_memory(
        goal="铁矿石现在怎么样？",
        final_answer="铁矿石目前处于下降通道。"
    )

    # 5. 验证模型被调用了
    assert mock_client_instance.chat.completions.create.called

    # 6. 验证记忆被存入
    memory = agent.recall()
    assert len(memory) > 0
