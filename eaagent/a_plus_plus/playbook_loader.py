import re
from pathlib import Path

def load_playbook(name="v3"):
    candidates = [
        f"artifacts/playbooks/{name}.md",
        f"artifacts/playbooks/{name}",
        f"artifacts/{name}.md",
        "artifacts/trading_playbook_v3.md",
    ]
    for p in candidates:
        path = Path(p)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            # 增强规则提取：抓取所有带编号的标题
            rules = re.findall(r'(?:^|\n)(?:###|\d+\.\d+|\d+\.)\s*(.+?)(?=\n|$)', content)
            rules = [r.strip() for r in rules if r.strip() and len(r) > 5]
            print(f"[Playbook] ✅ 加载成功 → {name} | 规则数: {len(rules)}")
            return content, rules[:15]  # 最多取15条，避免过长
    print("[Playbook] ⚠️ 未找到，使用默认")
    return "默认规则", ["量仓核心逻辑", "关键压力位", "波段操作"]

def build_playbook_prompt(): 
    content, _ = load_playbook()
    return content[:4000]

def get_relevant_playbook_rules(keywords=""):
    _, rules = load_playbook()
    return rules

def get_playbook_id(content=None):
    return "v3-20260628"
PLAYBOOK_CONTENT = load_playbook()[0]
