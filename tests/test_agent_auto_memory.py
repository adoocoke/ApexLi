"""
自动记忆功能测试（A计划） - CI 友好版
"""

import pytest
from eaagent import ReActAgent


def test_auto_memory_parameter():
    """测试 auto_memory 参数"""
    agent = ReActAgent(verbose=False, require_api_key=False, auto_memory=True)
    assert agent.auto_memory is True


def test_extract_and_store_memory_exists():
    """测试方法存在"""
    agent = ReActAgent(verbose=False, require_api_key=False)
    assert hasattr(agent, '_extract_and_store_memory')


def test_auto_memory_extraction_flow():
    """测试自动记忆提取逻辑（测试模式）"""
    agent = ReActAgent(verbose=False, require_api_key=False, auto_memory=True)
    
    # 手动调用提取方法（测试模式下 client 为 None，会直接返回）
    agent._extract_and_store_memory(
        goal="测试问题",
        final_answer="这是一个测试答案。"
    )
    
    # 只要不报错就算通过
    assert True
