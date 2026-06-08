from typing import Optional
import os

class PlaybookPromptBuilder:
    """
    负责加载 trading_playbook_v3.md 并构建增强的 System Prompt
    Playbook 默认从 artifacts/ 目录读取，不会提交到 GitHub
    """

    def __init__(self, playbook_path: Optional[str] = None):
        if playbook_path is None:
            # 优先从 artifacts 目录查找
            possible_paths = [
                "artifacts/trading_playbook_v3.md",
                "../artifacts/trading_playbook_v3.md",
                "trading_playbook_v3.md",
                os.path.join(os.path.dirname(__file__), "../../artifacts/trading_playbook_v3.md"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    playbook_path = path
                    break
            else:
                playbook_path = "artifacts/trading_playbook_v3.md"

        self.playbook_path = playbook_path
        self.playbook_content = self._load_playbook()

    def _load_playbook(self) -> str:
        try:
            with open(self.playbook_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "【警告】Playbook 文件未找到，请确认 artifacts/trading_playbook_v3.md 是否存在。"

    def build_system_prompt(self, rag_context: Optional[str] = None) -> str:
        base_prompt = f"""你是一位经验丰富的期货交易员，严格遵循以下《交易技能 Playbook》进行思考和决策。

{self.playbook_content}

请严格按照 Playbook 中的逻辑、定式和行为轨迹进行分析。
"""

        if rag_context:
            base_prompt += f"\n\n【当前相关规则片段】\n{rag_context}\n"

        base_prompt += """
当前任务：
请根据提供的市场观察（Observation），严格按照 ReAct 格式输出 Thought 和 Action。
"""
        return base_prompt
