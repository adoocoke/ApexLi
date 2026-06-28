from pathlib import Path
from typing import Tuple, List
import re

class PlaybookManager:
    """
    统一 Playbook 加载管理器
    - 支持本地开发（zen/dow/abu + v3）
    - 兼容 CI 环境（GitHub Actions runner 路径）
    - 提供规则提取、Prompt 构建等辅助功能
    """

    def load(self, name: str = "v3") -> Tuple[str, str]:
        """
        加载指定 Playbook
        优先级：
        1. artifacts/playbooks/{name}.md          (推荐新结构)
        2. artifacts/trading_playbook_v3.md       (旧 v3 结构，CI 依赖)
        3. 其他兜底路径
        """
        # 1. 新风格：zen / dow / abu
        if name in ["zen", "dow", "abu"]:
            p = Path(f"artifacts/playbooks/{name}.md")
            if p.exists():
                content = p.read_text(encoding="utf-8")
                print(f"[Playbook] ✅ 成功加载 → {name} ({p.name})")
                return content, name

        # 2. v3 及通用候选路径（兼容本地 + CI）
        candidates = [
            Path(f"artifacts/playbooks/{name}.md"),
            Path("artifacts/trading_playbook_v3.md"),
            Path("artifacts/playbooks/trading_playbook_v3.md"),
            Path("trading_playbook_v3.md"),
            # CI 环境下的绝对路径
            Path("/home/runner/work/ApexLi/ApexLi/artifacts/trading_playbook_v3.md"),
            Path("/home/runner/work/ApexLi/ApexLi/artifacts/playbooks/trading_playbook_v3.md"),
        ]

        for p in candidates:
            if p.exists():
                content = p.read_text(encoding="utf-8")
                print(f"[Playbook] ✅ 找到文件: {p}")
                return content, name

        # 3. 最后兜底
        print(f"[Playbook] ⚠️ 未找到 {name}，使用内置默认")
        return "# 默认空规则\n", name

    def get_rules(self, name: str = "v3", max_rules: int = 15) -> List[str]:
        """提取 Playbook 中的规则标题"""
        content, _ = self.load(name)
        rules = re.findall(r'(?:^|\n)(?:###|\d+\.\d+|\d+\.)\s*(.+?)(?=\n|$)', content)
        rules = [r.strip() for r in rules if r.strip() and len(r) > 5]
        return rules[:max_rules]

    def build_prompt(self, name: str = "v3", max_chars: int = 4000) -> str:
        """构建给 LLM 的 Playbook Prompt"""
        content, _ = self.load(name)
        return content[:max_chars]

    def get_id(self, name: str = "v3") -> str:
        """获取 Playbook 版本 ID"""
        return f"{name}-20260628"


# 全局单例
manager = PlaybookManager()


# ==================== 向后兼容层 ====================
def load_playbook(name="v3"):
    return manager.load(name)

def build_playbook_prompt():
    return manager.build_prompt()

def get_relevant_playbook_rules(keywords=""):
    return manager.get_rules()

def get_playbook_id(content=None):
    return manager.get_id()

PLAYBOOK_CONTENT = manager.load()[0]