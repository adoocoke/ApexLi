# data_gathering 节点重构计划（绞杀者模式）

## 1. 目标

将 `data_gathering` 节点从“直接调用 Python 函数”逐步迁移到 **LangChain 原生 Tool Calling** 方式。

使用 **绞杀者模式（Strangler Fig Pattern）** 进行渐进式重构，降低风险。

先在 `data_gathering` 做试点，验证 `@tool` + `bind_tools` 在项目中的实际效果。

## 2. 采用策略：绞杀者模式

- 保留原有逻辑作为 **Legacy Path（旧路径）**。
- 新增 **New Path（新路径）** 使用 `@tool` + `bind_tools`。
- 通过开关控制新旧路径切换。
- 逐步把流量切到新路径，最终完全替换旧逻辑。

## 3. 重构阶段

### 阶段 1：并行建设（推荐先做）

- 把 `data_gathering` 中用到的数据获取函数改成 `@tool` 形式。
- 在 `data_gathering` 节点内部实现双路径逻辑。
- 新增 `data_gathering_with_tools` 函数（新路径）。
- 通过环境变量 `USE_NATIVE_TOOL_CALLING` 控制走新路径还是旧路径。
- 初期默认走旧路径（`USE_NATIVE_TOOL_CALLING=false`）。

### 阶段 2：灰度验证

- 在测试环境开启新路径进行验证。
- 观察工具调用成功率、LLM 是否正确使用工具、返回结果是否正确。
- 可按 symbol 或 playbook 进行小范围灰度。

### 阶段 3：完全切换

- 确认新路径稳定后，将默认开关改为 `true`。
- 逐步删除旧路径代码（`data_gathering_legacy`）。
- 清理冗余代码。

### 阶段 4：架构升级（可选）

- 验证稳定后，考虑是否引入 `ToolNode` + 条件边，进一步规范化。

## 4. 具体实施步骤

### 步骤 1：工具标准化

在 `eaagent/a_plus_plus/tools.py` 中给相关函数加上 `@tool` 装饰器。

主要工具包括：
- `get_related_futures_daily`
- `get_futures_daily_recent`
- `get_futures_holding`
- `get_futures_basic`

### 步骤 2：修改 data_gathering 节点

在 `eaagent/a_plus_plus/nodes/data_gathering.py` 中实现双路径逻辑。

新增 `data_gathering_with_tools` 函数，使用 `llm.bind_tools(tools)`，判断是否有 `tool_calls` 并执行对应工具。

### 步骤 3：添加开关控制

推荐使用环境变量控制：

```bash
export USE_NATIVE_TOOL_CALLING=true
```

### 步骤 4：测试与验证

重点验证以下几点：
- 单轮和多轮迭代是否正常
- 工具调用是否成功
- 工具返回结果是否正确写入 `state["extra_data"]`
- 是否能正确回滚到旧逻辑

## 5. 文件变更清单

| 文件路径                                      | 操作     | 说明                     |
|-----------------------------------------------|----------|--------------------------|
| `eaagent/a_plus_plus/tools.py`                | 修改     | 添加 `@tool` 装饰器      |
| `eaagent/a_plus_plus/nodes/data_gathering.py` | 修改     | 实现双路径逻辑           |
| `eaagent/a_plus_plus/graph.py`                | 可选修改 | 按需导入新函数           |
| `.env` 或启动脚本                             | 新增变量 | 添加开关控制             |

## 6. 风险与回滚策略

- **主要风险**：Grok 对工具调用的稳定性（尤其是复杂参数时）
- **回滚方式**：将环境变量 `USE_NATIVE_TOOL_CALLING` 设置为 `false` 即可立即切回旧逻辑
- **建议**：先在本地或测试环境充分验证，再逐步上线

## 7. 后续规划

- `data_gathering` 试点成功后，再对 `signal_generation` 进行类似改造。
- 最终目标：所有工具调用统一使用原生 Tool Calling 方式。