from pathlib import Path
from typing import Tuple

class PlaybookManager:
    def load(self, name: str = "v3") -> Tuple[str, str]:
        """
        兼容本地开发 + CI 环境
        - zen/dow/abu 优先从 artifacts/playbooks/ 加载
        - v3 兼容多种路径（包括 CI 的 /home/runner/work/... 路径）
        """
        # 1. 新风格：zen / dow / abu
        if name in ["zen", "dow", "abu"]:
            p = Path(f"artifacts/playbooks/{name}.md")
            if p.exists():
                content = p.read_text(encoding="utf-8")
                print(f"[Playbook] ✅ 成功加载 → {name} ({p.name})")
                return content, name

        # 2. v3 的多种候选路径（兼容本地 + CI）
        candidates = [
            Path(f"artifacts/playbooks/{name}.md"),
            Path("artifacts/trading_playbook_v3.md"),
            Path("artifacts/playbooks/trading_playbook_v3.md"),
            Path("trading_playbook_v3.md"),
            # CI 环境下的绝对路径（GitHub Actions runner）
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

manager = PlaybookManager()
