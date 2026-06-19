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


class IdOnlyStrategy(PlaybookInjectionStrategy):
    """只发送 Playbook ID（后续轮次使用）"""

    def get_system_prompt(self, playbook_content: str, playbook_id: str) -> str:
        return f"请继续使用 ID 为 {playbook_id} 的 Playbook 进行分析。"
