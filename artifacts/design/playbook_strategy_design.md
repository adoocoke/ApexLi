# Playbook 注入策略设计（Strategy Pattern）

## 1. 背景与问题

当前在 `graph.py` 中，我们把 Playbook 内容直接塞进 system prompt 发送给 LLM。这种方式存在以下问题：

- 每次调用（尤其是多轮分析）都会重复发送大量 Playbook 内容，浪费 Token。
- 难以灵活切换不同的注入方式（完整版 / 精简核心规则版 / 只发 ID 版）。
- 未来如果要支持 RAG、版本管理、动态裁剪等需求，代码会变得混乱。

因此，我们需要把 **“如何把 Playbook 发给 LLM”** 这个行为抽象成可插拔的策略。

---

## 2. 设计模式选择

**推荐使用：Strategy Pattern（策略模式）**

### 为什么选择 Strategy Pattern？

| 设计模式         | 适用性 | 说明 |
|------------------|--------|------|
| **Strategy Pattern** | ★★★★★ | 最适合“算法族可互换”的场景 |
| State Pattern      | ★★     | 更适合状态驱动的行为变化 |
| Factory Pattern    | ★★★    | 可作为 Strategy 的辅助（创建策略） |
| Template Method    | ★      | 不太适合 |

**Strategy Pattern** 的核心优势：
- 把“Playbook 注入逻辑”封装成独立策略类。
- 支持运行时动态切换不同策略。
- 符合开闭原则（对扩展开放，对修改关闭）。
- 代码结构清晰，易于维护和测试。

---

## 3. 整体设计

### 3.1 策略接口

```python
from abc import ABC, abstractmethod

class PlaybookInjectionStrategy(ABC):
    """Playbook 注入策略接口"""

    @abstractmethod
    def get_system_prompt(self, playbook_content: str, playbook_id: str, **kwargs) -> str:
        """
        返回要发送给 LLM 的 system prompt 内容
        """
        pass
```

### 3.2 具体策略实现

| 策略类                        | 说明                                      | 适用场景               |
|-------------------------------|-------------------------------------------|------------------------|
| `FullPlaybookStrategy`        | 发送完整 Playbook + ID                    | 第一次交互             |
| `CoreRulesStrategy`           | 只发送精简后的核心规则 + ID               | 想节省 Token           |
| `IdOnlyStrategy`              | 只发送 Playbook ID（假设 LLM 已记住）     | 后续多轮分析           |
| `SummarizedStrategy`          | 发送 Playbook 摘要版本 + ID               | 平衡效果与成本         |
| `RagPlaybookStrategy`         | 通过检索只发送相关片段（未来扩展）        | 大型 Playbook 场景     |

**示例实现**：

```python
class FullPlaybookStrategy(PlaybookInjectionStrategy):
    def get_system_prompt(self, playbook_content: str, playbook_id: str, **kwargs) -> str:
        return (
            f"{playbook_content}\n\n"
            f"请记住当前 Playbook 的 ID 为：{playbook_id}。\n"
            f"后续交互中如果 Playbook 没有变化，请直接使用该 ID，无需重复发送完整内容。"
        )


class CoreRulesStrategy(PlaybookInjectionStrategy):
    def get_system_prompt(self, playbook_content: str, playbook_id: str, **kwargs) -> str:
        core_rules = self._extract_core_rules(playbook_content)
        return (
            f"以下是 Playbook 的核心规则：\n{core_rules}\n\n"
            f"请记住当前 Playbook 的 ID 为：{playbook_id}。"
        )

    def _extract_core_rules(self, content: str) -> str:
        # TODO: 可实现简单规则提取逻辑
        return content[:1500]   # 示例：截取前1500字符作为核心


class IdOnlyStrategy(PlaybookInjectionStrategy):
    def get_system_prompt(self, playbook_content: str, playbook_id: str, **kwargs) -> str:
        return f"请继续使用 ID 为 {playbook_id} 的 Playbook 进行分析，不要要求重复发送内容。"
```

---

## 4. 在 Graph 中的使用方式

我们可以在 `initialize_state` 或新增的 `playbook_injection` 节点中使用策略：

```python
def initialize_state(state: TAState) -> TAState:
    if load_playbook():
        state["playbook_used"] = True
        playbook_id = get_playbook_id(PLAYBOOK_CONTENT)
        state["playbook_id"] = playbook_id

        # 根据配置或状态选择策略
        strategy = self._get_strategy(state)   # 可从配置或 state 中获取

        system_prompt = strategy.get_system_prompt(
            PLAYBOOK_CONTENT, 
            playbook_id,
            is_first_time=not state.get("playbook_content_sent", False)
        )

        state["messages"].append({"role": "system", "content": system_prompt})
        state["playbook_content_sent"] = True

    return state

def _get_strategy(self, state: TAState) -> PlaybookInjectionStrategy:
    mode = os.getenv("PLAYBOOK_INJECTION_MODE", "full")  # 可通过环境变量切换

    if mode == "full":
        return FullPlaybookStrategy()
    elif mode == "core":
        return CoreRulesStrategy()
    elif mode == "id_only":
        return IdOnlyStrategy()
    else:
        return FullPlaybookStrategy()
```

---

## 5. 切换策略的方式

我们可以通过以下几种方式灵活切换策略：

1. **环境变量**（推荐开发阶段使用）
   ```bash
   PLAYBOOK_INJECTION_MODE=core python -m eaagent.a_plus_plus.graph
   ```

2. **配置文件**（`config.py` 或 `settings.yaml`）

3. **运行时动态传入**（通过 State 或外部参数）

4. **Factory + 配置中心**（生产环境推荐）

---

## 6. 优势总结

- **可扩展性强**：新增策略只需实现接口，无需修改主流程。
- **符合开闭原则**：对扩展开放，对修改关闭。
- **测试友好**：可以轻松为不同策略编写单元测试。
- **Token 优化**：通过 `IdOnlyStrategy` 和 `CoreRulesStrategy` 可显著降低 Prompt 长度。
- **易于演进**：未来可轻松接入 RAG、版本管理等高级功能。

---

## 7. 后续演进方向

- 增加 `SummarizedStrategy`（使用 LLM 自动总结 Playbook）
- 增加 `RagPlaybookStrategy`（基于向量检索动态注入相关规则）
- 支持 Playbook 版本管理（不同 ID 对应不同版本）
- 在 LangGraph 中使用 `Runnable` / `Configurable` 实现更优雅的策略切换

---

## 8. 文件建议结构

```
eaagent/
├── strategies/
│   ├── __init__.py
│   └── playbook_strategies.py      # 存放所有策略类
├── playbook_loader.py
└── graph.py
```

---

**文档版本**：v1.0  
**日期**：2026-06-18  
**作者**：Grok + 用户协作设计
