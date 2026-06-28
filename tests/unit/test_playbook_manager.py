import pytest
from unittest.mock import patch
from eaagent.playbooks.manager import (
    PlaybookManager,
    manager,
    load_playbook,
    build_playbook_prompt,
    get_relevant_playbook_rules,
    get_playbook_id,
)


class TestPlaybookManager:
    """PlaybookManager 核心功能测试"""

    def test_get_id(self):
        m = PlaybookManager()
        assert m.get_id("v3") == "v3-20260628"
        assert m.get_id("zen") == "zen-20260628"

    def test_build_prompt(self):
        m = PlaybookManager()
        prompt = m.build_prompt("v3", max_chars=100)
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    @patch("eaagent.playbooks.manager.Path.exists")
    @patch("eaagent.playbooks.manager.Path.read_text")
    def test_load_zen_success(self, mock_read_text, mock_exists):
        mock_exists.return_value = True
        mock_read_text.return_value = "# 缠论 Playbook\n## 核心原则\n1. 只做有背驰的买卖点"
        m = PlaybookManager()
        content, name = m.load("zen")
        assert name == "zen"
        assert "缠论" in content

    @patch("eaagent.playbooks.manager.Path.exists")
    @patch("eaagent.playbooks.manager.Path.read_text")
    def test_load_dow_success(self, mock_read_text, mock_exists):
        mock_exists.return_value = True
        mock_read_text.return_value = "# 道氏理论 Playbook\n趋势是朋友"
        m = PlaybookManager()
        content, name = m.load("dow")
        assert name == "dow"

    @patch("eaagent.playbooks.manager.Path.exists")
    def test_load_fallback_when_not_found(self, mock_exists):
        mock_exists.return_value = False
        m = PlaybookManager()
        content, name = m.load("nonexistent")
        assert name == "nonexistent"
        assert "默认空规则" in content

    def test_get_rules(self):
        """测试 get_rules 能正确提取规则"""
        m = PlaybookManager()
        with patch.object(m, "load") as mock_load:
            mock_load.return_value = (
                "# 测试规则\n1. 第一条核心规则\n2. 第二条规则\n### 第三条重要规则\n",
                "v3"
            )
            rules = m.get_rules("v3", max_rules=10)
            assert len(rules) >= 2
            assert any("第一条" in r or "核心规则" in r for r in rules)

    def test_backward_compatible_functions(self):
        content, name = load_playbook("v3")
        assert isinstance(content, str)
        assert name == "v3"

        prompt = build_playbook_prompt()
        assert isinstance(prompt, str)

        rules = get_relevant_playbook_rules()
        assert isinstance(rules, list)

        pid = get_playbook_id()
        assert isinstance(pid, str)


class TestGlobalManager:
    def test_global_manager_is_singleton(self):
        from eaagent.playbooks.manager import manager as m1
        from eaagent.playbooks.manager import manager as m2
        assert m1 is m2

    def test_global_manager_load(self):
        content, name = manager.load("v3")
        assert isinstance(content, str)
        assert name == "v3"
