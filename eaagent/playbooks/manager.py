from typing import Dict, List
from pathlib import Path

class PlaybookManager:
    def __init__(self):
        self.registry = {}

    def register(self, name: str, filepath: str, description: str):
        self.registry[name] = {
            "path": filepath,
            "desc": description
        }

    def load(self, name: str = "v3"):
        if name not in self.registry:
            name = "v3"
        path = self.registry[name]["path"]
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[Playbook] ✅ 已切换到 {name} | {self.registry[name]['desc']}")
            return content, name
        else:
            print(f"[Playbook] ⚠️ 未找到 {name}，回退到 v3")
            return open("artifacts/trading_playbook_v3.md", "r", encoding="utf-8").read(), "v3"

manager = PlaybookManager()
manager.register("v3", "artifacts/trading_playbook_v3.md", "沪上十二少量仓风格")
manager.register("zen", "artifacts/playbooks/zen.md", "缠论风格（待创建）")
manager.register("dow", "artifacts/playbooks/dow.md", "道氏理论风格（待创建）")
manager.register("abu", "artifacts/playbooks/abu.md", "阿布行为学风格（待创建）")

def get_playbook(name="v3"):
    return manager.load(name)
