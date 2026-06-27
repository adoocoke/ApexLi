import os
import re
from pathlib import Path
from typing import List, Tuple

def load_playbook() -> Tuple[str, List[str]]:
    paths = [
        "artifacts/trading_playbook_v3.md",
        "artifacts/playbooks/trading_playbook_v3.md",
        "trading_playbook_v3.md"
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[Playbook] ✅ 成功加载: {p}")
            rules = re.findall(r'###\s*(.+?)(?=\n|$)', content)
            return content, [r.strip() for r in rules if r.strip()]
    print("[Playbook] ⚠️ 未找到文件，使用默认规则")
    return "默认规则", ["量仓核心逻辑", "关键压力位量仓观察", "波段操作与减仓信号"]


def build_playbook_prompt(max_length: int = 3800) -> str:
    content, _ = load_playbook()
    if len(content) > max_length:
        content = content[:max_length] + "\n...(截断)"
    return content


def get_relevant_playbook_rules(keywords: str = "") -> List[str]:
    _, rules = load_playbook()
    return rules[:5]


def get_playbook_id(content=None) -> str:   # 增加兼容参数
    return "v3.0-20260625"


# 兼容旧代码（graph.py 仍在调用 PLAYBOOK_CONTENT）
PLAYBOOK_CONTENT = load_playbook()[0]
