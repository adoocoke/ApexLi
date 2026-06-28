from pathlib import Path

class PlaybookManager:
    def load(self, name="v3"):
        # 支持多种命名和位置
        candidates = [
            f"artifacts/playbooks/{name}.md",
            f"artifacts/playbooks/{name}",
            f"artifacts/{name}.md",
            "artifacts/trading_playbook_v3.md",   # 最终兜底
        ]
        
        for p in candidates:
            path = Path(p)
            if path.exists():
                content = path.read_text(encoding="utf-8")
                print(f"[Playbook] ✅ 成功加载 → {name} ({path.name})")
                return content, name
        
        print(f"[Playbook] ⚠️ 未找到 {name}，使用 v3 兜底")
        content = Path("artifacts/trading_playbook_v3.md").read_text(encoding="utf-8")
        return content, "v3"

manager = PlaybookManager()
