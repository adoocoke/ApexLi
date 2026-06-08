from typing import Optional, Dict, Any
from eaagent.agent import ReActAgent
from .prompt_builder import PlaybookPromptBuilder


class APlusPlusReActAgent(ReActAgent):
    """
    继承 eaagent 的 ReActAgent，并注入 A++ Playbook
    """

    def __init__(self, playbook_path: str = "trading_playbook_v3.md", **kwargs):
        # 注意：这里不再传 model_name，全部透传给父类
        super().__init__(**kwargs)
        self.prompt_builder = PlaybookPromptBuilder(playbook_path)
        self.playbook_rules: Optional[Dict[str, Any]] = None

    def load_playbook(self):
        """加载 Playbook"""
        self.playbook_rules = {"status": "loaded", "version": "v3.0"}

    def build_enhanced_prompt(self, rag_context: Optional[str] = None) -> str:
        """构建注入 Playbook 的 Prompt"""
        return self.prompt_builder.build_system_prompt(rag_context=rag_context)

    def run_with_playbook(self, goal: str, rag_context: Optional[str] = None) -> str:
        """
        增强版 run 方法，自动注入 Playbook
        """
        enhanced_prompt = self.build_enhanced_prompt(rag_context)
        full_goal = f"{enhanced_prompt}\n\n用户目标：{goal}"
        return self.run(full_goal)

    def remember_feedback(self, feedback: Dict[str, Any]):
        """记录人类反馈，用于后续 AIFED 成长"""
        print(f"[AIFED] 收到反馈: {feedback}")
