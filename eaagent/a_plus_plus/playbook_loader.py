from eaagent.playbooks.manager import get_playbook, manager

def load_playbook(name="v3"):
    content, _ = get_playbook(name)
    print(f"[Playbook] ✅ 加载 {name}")
    return content, ["量仓核心逻辑", "关键位置量仓观察", "主动放弃原则"]

def build_playbook_prompt(name="v3", max_length=4000):
    content, _ = get_playbook(name)
    return content[:max_length] if len(content) > max_length else content

def get_relevant_playbook_rules(keywords=""):
    return ["2.1 量仓分析核心逻辑", "2.3 趋势判断与行情选择", "2.4 风控与执行规则"]

def get_playbook_id(name="v3"):
    return f"{name}-20260628"

# 兼容旧代码
PLAYBOOK_CONTENT = load_playbook()[0]

print("✅ playbook_loader.py 已修复兼容性")
