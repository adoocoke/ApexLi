from eaagent.playbooks.manager import get_playbook, manager

def load_playbook(name="v3"):
    content, name = get_playbook(name)
    return content, [name]

def build_playbook_prompt(name="v3", max_length=4000):
    content, _ = get_playbook(name)
    return content[:max_length]

def get_playbook_id(name="v3"):
    return f"{name}-20260628"

print("[Playbook Manager] ✅ 初始化完成，支持 v3 / zen / dow / abu 切换")
