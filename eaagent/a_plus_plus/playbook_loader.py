import os
import re
import hashlib

PLAYBOOK_CONTENT = ""
PLAYBOOK_LOADED = False
PLAYBOOK_RULES = []


def get_playbook_id(content: str) -> str:
    """根据 Playbook 内容生成稳定 ID"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]


def load_playbook() -> bool:
    global PLAYBOOK_CONTENT, PLAYBOOK_LOADED, PLAYBOOK_RULES

    possible_paths = [
        "artifacts/trading_playbook_v3.md",
        "artifacts/playbooks/trading_playbook_v3.md",
        "trading_playbook_v3.md",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    PLAYBOOK_CONTENT = f.read()

                PLAYBOOK_RULES = re.findall(r'###\s*(.+?)(?=\n|$)', PLAYBOOK_CONTENT)
                if not PLAYBOOK_RULES:
                    PLAYBOOK_RULES = ["量仓变化优先", "多时间框架一致性", "严格止损纪律"]

                PLAYBOOK_LOADED = True
                print(f"[Playbook] ✅ 成功加载: {path}（共 {len(PLAYBOOK_RULES)} 条关键规则）")
                return True
            except Exception as e:
                print(f"[Playbook] 读取失败: {e}")
                return False

    print("[Playbook] ❌ 未找到 trading_playbook_v3.md")
    return False


def build_playbook_prompt() -> str:
    if not PLAYBOOK_LOADED or not PLAYBOOK_CONTENT:
        return "你是一个专业的期货技术分析师，请严格遵守交易纪律进行分析。"

    core_content = PLAYBOOK_CONTENT[:3500]
    return f"""你是一个专业的期货技术分析师，请严格遵守以下 Playbook 规则进行分析：

{core_content}

分析要求：
- 必须关注量仓变化
- 多时间框架信号需保持一致性
- 必须设置合理止损
- 信息不足时主动放弃判断
"""


def get_relevant_playbook_rules(context: str = "") -> list:
    if not PLAYBOOK_LOADED:
        return []

    relevant = []
    context_lower = context.lower()

    for rule in PLAYBOOK_RULES:
        rule_lower = rule.lower()
        if any(kw in context_lower for kw in ["量", "仓", "止损", "时间框架", "支撑", "阻力"]):
            if any(kw in rule_lower for kw in ["量", "仓", "止损", "时间", "框架"]):
                relevant.append(rule)

    return relevant[:3] if relevant else PLAYBOOK_RULES[:3]
