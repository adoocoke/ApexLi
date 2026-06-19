# Development Guide

## 如何新增一个 Node

### 步骤

1. 在 `eaagent/a_plus_plus/nodes/` 目录下创建新文件（如 `my_new_node.py`）
2. 定义函数，接收 `TAState` 并返回 `TAState`
3. 在 `nodes/__init__.py` 中导出该函数
4. 在 `graph.py` 的 `build_graph()` 中注册节点并添加边
5. 编写对应测试
6. 更新 `docs/user-journey-and-stories.md`（如有新 Story）

### 示例

```python
# nodes/my_new_node.py
from eaagent.a_plus_plus.types import TAState

def my_new_node(state: TAState) -> TAState:
    # 业务逻辑
    return state
```

## 注意事项

- 节点应保持单一职责
- 尽量复用 `call_llm` 和结构化输出
- 新节点建议先写测试再实现逻辑