"""
测试 Playbook Strategy Pattern
"""
import pytest
from eaagent.a_plus_plus.strategies.playbook_strategies import (
    FullPlaybookStrategy,
    CoreRulesStrategy,
    IdOnlyStrategy,
)


class TestPlaybookStrategies:

    @pytest.fixture
    def sample_playbook(self):
        # 使用较长的示例 Playbook
        return """### 量仓分析核心逻辑（最强武器）
持仓稳步增加是趋势持续的重要信号。持仓减少则可能是趋势反转信号。

### 关键压力位量仓观察 + 预测 vs 交易
价格接近压力位时，必须观察量仓变化。不能仅凭预测交易。

### 波段操作与减仓信号 + 系统选择
反弹至压力区可考虑减仓。严格执行波段操作纪律。

### 主动放弃原则
当信息不足或置信度过低时，应主动放弃判断，等待更好机会。"""

    def test_full_playbook_strategy(self, sample_playbook):
        strategy = FullPlaybookStrategy()
        prompt = strategy.get_system_prompt(sample_playbook, "abc123")

        assert "量仓分析核心逻辑" in prompt
        assert "请记住当前 Playbook 的 ID 为：abc123" in prompt
        assert sample_playbook[:100] in prompt   # 完整内容应被包含

    def test_core_rules_strategy(self, sample_playbook):
        strategy = CoreRulesStrategy()
        prompt = strategy.get_system_prompt(sample_playbook, "abc123")

        assert "核心规则" in prompt or "精简" in prompt
        assert "请记住当前 Playbook 的 ID 为：abc123" in prompt
        # CoreRulesStrategy 应该比 Full 短（当前实现是截取前2000字符）
        assert len(prompt) <= len(sample_playbook) + 300

    def test_id_only_strategy(self, sample_playbook):
        strategy = IdOnlyStrategy()
        prompt = strategy.get_system_prompt(sample_playbook, "abc123")

        assert "ID 为 abc123" in prompt
        assert "量仓分析核心逻辑" not in prompt
        assert len(prompt) < 80

    def test_different_strategies_return_different_prompts(self, sample_playbook):
        full = FullPlaybookStrategy().get_system_prompt(sample_playbook, "id1")
        core = CoreRulesStrategy().get_system_prompt(sample_playbook, "id1")
        id_only = IdOnlyStrategy().get_system_prompt(sample_playbook, "id1")

        assert full != core
        assert core != id_only
        assert full != id_only
