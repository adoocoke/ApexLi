from pathlib import Path

class PlaybookManager:
    def load(self, name="v3"):
        paths = {
            "v3": "artifacts/trading_playbook_v3.md",
            "zen": "artifacts/playbooks/zen.md",
            "dow": "artifacts/playbooks/dow.md",
            "abu": "artifacts/playbooks/abu.md"
        }
        path = Path(paths.get(name, paths["v3"]))
        if path.exists():
            content = path.read_text(encoding="utf-8")
            print(f"[Playbook] ✅ 成功切换 → {name}")
            return content, name
        print(f"[Playbook] ⚠️ {name} 未找到，使用 v3")
        content = Path("artifacts/trading_playbook_v3.md").read_text(encoding="utf-8")
        return content, "v3"

manager = PlaybookManager()
