import os
import requests
from pathlib import Path
from typing import Tuple

class PlaybookManager:
    def load(self, name: str = "v3") -> Tuple[str, str]:
        """
        兼容本地开发 + CI 远程加载
        - 本地优先加载 artifacts/playbooks/ 下的 zen/dow/abu
        - CI 环境下（有 PLAYBOOK_REPO_TOKEN），v3 从 adoocoke/trading-playbooks 远程加载
        """
        token = os.getenv("PLAYBOOK_REPO_TOKEN")

        # === CI 模式：远程加载 v3 ===
        if name == "v3" and token:
            try:
                content = self._load_from_github(
                    owner="adoocoke",
                    repo="trading-playbooks",
                    path="trading_playbook_v3.md",
                    token=token
                )
                print("[Playbook] ✅ 从远程 trading-playbooks 加载 v3（CI模式）")
                return content, "v3"
            except Exception as e:
                print(f"[Playbook] ⚠️ 远程加载失败: {e}，尝试本地兜底")

        # === 本地模式 ===
        local_candidates = [
            f"artifacts/playbooks/{name}.md",
            f"artifacts/playbooks/{name}",
            f"artifacts/{name}.md",
            "artifacts/trading_playbook_v3.md",
        ]

        for p in local_candidates:
            path = Path(p)
            if path.exists():
                content = path.read_text(encoding="utf-8")
                print(f"[Playbook] ✅ 成功加载 → {name} ({path.name})")
                return content, name

        # 最后兜底
        print(f"[Playbook] ⚠️ 未找到 {name}，使用 v3 兜底")
        content = Path("artifacts/trading_playbook_v3.md").read_text(encoding="utf-8")
        return content, "v3"

    def _load_from_github(self, owner: str, repo: str, path: str, token: str) -> str:
        """通过 GitHub API 加载私有仓库文件"""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text

manager = PlaybookManager()
