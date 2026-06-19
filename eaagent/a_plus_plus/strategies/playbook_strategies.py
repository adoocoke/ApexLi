from abc import ABC, abstractmethod


class PlaybookInjectionStrategy(ABC):
    """Playbook 注入策略基类"""

    @abstractmethod
    def get_system_prompt(self, playbook_content: str, playbook_id: str) -> str:
        pass


class FullPlaybookStrategy(PlaybookInjectionStrategy):
    """发送完整 Playbook + ID（第一次使用）"""

    def get_system_prompt(self, playbook_content: str, playbook_id: str) -> str:
        return (
            f"{playbook_content}\n\n"
            f"请记住当前 Playbook 的 ID 为：{playbook_id}。\n"
            f"后续交互中如果 Playbook 没有变化，请直接使用该 ID，无需重复发送完整内容。"
        )


class CoreRulesStrategy(PlaybookInjectionStrategy):
    """只发送精简后的核心规则 + ID（节省 Token）"""

    def get_system_prompt(self, playbook_content: str, playbook_id: str) -> str:
        core_rules = self._extract_core_rules(playbook_content)
        return (
            f"以下是 Playbook 的核心规则（已精简）：\n\n{core_rules}\n\n"
            f"请记住当前 Playbook 的 ID 为：{playbook_id}。\n"
            f"后续请直接使用该 ID 进行分析。"
        )

    def _extract_core_rules(self, content: str, max_chars: int = 2000) -> str:
        """简单提取核心规则（可后续优化为更智能的提取）"""
        # 这里先简单截取前 2000 字符作为核心规则
        # 后续可以改成按 "###" 标题提取关键章节
        return content[:max_chars].strip()


class IdOnlyStrategy(PlaybookInjectionStrategy):
    """只发送 Playbook ID（后续轮次使用）"""

    def get_system_prompt(self, playbook_content: str, playbook_id: str) -> str:
        return f"请继续使用 ID 为 {playbook_id} 的 Playbook 进行分析。"
