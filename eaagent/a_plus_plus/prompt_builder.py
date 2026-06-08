from typing import Optional

class PlaybookPromptBuilder:
    """
    负责加载 trading_playbook_v3.md 并构建增强的 System Prompt
    """

    def __init__(self, playbook_path: str = "trading_playbook_v3.md"):
        self.playbook_path = playbook_path
        self.playbook_content = self._load_playbook()

    def _load_playbook(self) -> str:
        """加载 Playbook 全文"""
        try:
            with open(self.playbook_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "Playbook 文件未找到，请确认路径。"

    def build_system_prompt(self, rag_context: Optional[str] = None) -> str:
        """
        构建注入 Playbook 的 System Prompt
        """
        base_prompt = f"""你是一位经验丰富的期货交易员，风格严格遵循以下《交易技能 Playbook》。

{self.playbook_content}

请严格按照 Playbook 中的逻辑、定式和行为轨迹进行思考和决策。
"""

        if rag_context:
            base_prompt += f"\n\n【当前相关规则片段（RAG）】\n{rag_context}\n"

        base_prompt += """
当前任务：
你将收到市场观察（Observation），请严格按照 ReAct 格式输出：
Thought: （用 Playbook 风格进行深度分析）
Action: （给出具体交易建议或观望理由）

请保持思考的逻辑性和一致性。
"""
        return base_prompt
