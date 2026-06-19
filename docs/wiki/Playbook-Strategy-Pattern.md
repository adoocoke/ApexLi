# Playbook Strategy Pattern

## 背景
传统方式是将整个 Playbook 塞进 Prompt，导致 Token 消耗大且难以控制风格。

## 解决方案
我们采用 **Strategy Pattern** 实现三种 Playbook 注入方式：

| 策略                    | 说明                              | 适用场景             | Token 消耗 |
|---------------------------|-----------------------------------------|--------------------------------|---------------|
| `FullPlaybookStrategy`    | 发送完整 Playbook + ID          | 第一次分析             | 高            |
| `CoreRulesStrategy`       | 只发送精简后的核心规则 + ID | 日常使用（推荐）   | 中            |
| `IdOnlyStrategy`          | 只发送 Playbook ID                | 后续多轮分析         | 低            |

## 使用方式

```bash
# 默认（完整版）
python -m eaagent.a_plus_plus.graph

# 使用核心规则版
PLAYBOOK_STRATEGY=core python -m eaagent.a_plus_plus.graph
```

## 设计优势

- 降低 Token 消耗
- 让多轮分析更高效
- 保持 Playbook 规则的可追渲性