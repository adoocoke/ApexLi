"""
MemoryManager (SQLite) 单元测试
"""

import os
import pytest
from eaagent.memory import MemoryManager


@pytest.fixture
def mem():
    """每个测试使用独立的临时数据库"""
    test_db = "test_memory_temp.db"
    m = MemoryManager(db_file=test_db)
    yield m
    m.close()
    if os.path.exists(test_db):
        os.remove(test_db)


def test_remember_and_recall(mem):
    mem.remember("铁矿石趋势", "目前处于下降通道")
    assert mem.recall("铁矿石趋势") == "目前处于下降通道"


def test_recall_all(mem):
    mem.remember("key1", "value1")
    mem.remember("key2", "value2")
    all_mem = mem.recall()
    assert "key1" in all_mem
    assert "key2" in all_mem


def test_persistence(mem):
    """测试持久化：重启后还能读到"""
    mem.remember("持久化测试", "应该能保存")
    mem.close()

    # 重新打开同一个数据库
    mem2 = MemoryManager(db_file=mem.db_file)
    assert mem2.recall("持久化测试") == "应该能保存"
    mem2.close()


def test_list_all(mem):
    mem.remember("a", "1")
    mem.remember("b", "2")
    all_list = mem.list_all()
    assert len(all_list) == 2
    assert all_list[0]["key"] in ["a", "b"]


def test_clear(mem):
    mem.remember("要删除的", "内容")
    mem.clear()
    assert mem.recall("要删除的") == ""
