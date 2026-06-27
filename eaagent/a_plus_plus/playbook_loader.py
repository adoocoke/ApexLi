import os
from pathlib import Path
from typing import Tuple, List

def find_playbook_file() -> Path:
    candidates = [
        Path("artifacts/trading_playbook_v3.md"),
        Path("artifacts/playbooks/trading_playbook_v3.md"),
        Path("trading_playbook_v3.md"),
        Path("/home/runner/work/ApexLi/ApexLi/artifacts/trading_playbook_v3.md"),  # CI 路径
    ]
    for p in candidates:
        if p.exists():
            print(f"[Playbook] ✅ 找到文件: {p}")
            return p
    print("[Playbook] ⚠️ 未找到文件，使用内置默认")
    return None

def load_playbook(name="v3") -> Tuple[str, List[str]]:
    file = find_playbook_file()
    if file and file.exists():
        content = file.read_text(encoding="utf-8")
    else:
        content = """### 2.1 量仓分析核心逻辑
### 2.3 趋势判断与行情选择
### 2.4 风控与执行规则"""

    rules = ["2.1 量仓分析核心逻辑", "2.3 趋势判断与行情选择", "2.4 风控与执行规则"]
    print(f"[Playbook] ✅ 加载成功 | 规则数: {len(rules)}")
    return content, rules


def build_playbook_prompt(name="v3", max_length=4000):
    content, _ = load_playbook(name)
    return content[:max_length] if len(content) > max_length else content


def get_relevant_playbook_rules(keywords=""):
    return ["2.1 量仓分析核心逻辑", "2.3 趋势判断与行情选择", "2.4 风控与执行规则"]


def get_playbook_id(name="v3"):
    return f"{name}-20260628"


# 兼容旧代码
PLAYBOOK_CONTENT, _ = load_playbook()
print("✅ playbook_loader.py 已完全兼容本地 + CI")
