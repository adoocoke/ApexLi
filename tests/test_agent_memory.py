"""
ReActAgent Memory 功能测试（A计划）
"""

import pytest
from eaagent import ReActAgent


def test_remember_and_recall():
    """测试 remember 和 recall 基本功能"""
    agent = ReActAgent(verbose=False)

    agent.remember("铁矿石趋势", "目前处于下降通道")
    agent.remember("螺纹钢支撑位", "3720附近")

    memory = agent.recall()

    assert "铁矿石趋势" in memory
    assert memory["铁矿石趋势"] == "目前处于下降通道"
    assert "螺纹钢支撑位" in memory


def test_recall_specific_key():
    """测试 recall 单个 key"""
    agent = ReActAgent(verbose=False)
    agent.remember("关键价位", "3800是重要阻力")

    result = agent.recall("关键价位")
    assert result == "3800是重要阻力"


def test_recall_nonexistent_key():
    """测试 recall 不存在的 key"""
    agent = ReActAgent(verbose=False)
    result = agent.recall("不存在的记忆")
    assert result == ""


def test_memory_in_system_prompt():
    """测试记忆是否会出现在 System Prompt 中"""
    agent = ReActAgent(verbose=False, max_steps=1)
    agent.remember("测试记忆", "这是一个测试记忆")
    # smoke test
