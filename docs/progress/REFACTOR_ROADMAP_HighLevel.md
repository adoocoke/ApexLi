# ApexLi LangGraph 重构路线图（High Level）

## 1. 总体目标

将当前以 **Prompt Engineering + 手动解析** 为主的工具调用方式，逐步迁移到 **LangChain 原生 Tool Calling + LangGraph 规范结构**，提升系统的可维护性、稳定性和扩展性。

核心原则：**使用绞杀者模式（Strangler Fig Pattern）进行渐进式重构**，避免大爆炸式改造。

## 2. 核心问题与痛点

- `signal_generation` 节点过于庞大，职责不清晰
- 工具调用依赖大量 Prompt 描述，维护成本高
- Grok 的工具调用能力未被充分利用
- 新增工具或修改逻辑时成本较高
- 多轮迭代 + 工具调用的闭环不够规范

## 3. 重构策略：绞杀者模式（Strangler Fig）

- **不一次性重写**整个 `signal_generation`
- **逐步替换**旧的 Prompt-based 工具调用逻辑
- 新老逻辑并存，通过开关或条件控制切换
- 优先在低风险节点试点，再逐步扩展到核心节点

## 4. 整体重构阶段规划

### 阶段 0：准备与试点（当前）
- 完成 `data_gathering` 节点的试点改造（已制定详细计划）
- 验证 `@tool` + `bind_tools` + 节点内工具执行的可行性
- 建立双路径机制（Legacy Path + New Path）

### 阶段 1：工具层标准化
- 将所有 LLM 可调用函数统一使用 `@tool` 装饰器定义
- 建立统一的 `tools` 列表
- 完善工具的 docstring 和类型注解

### 阶段 2：LLM 调用层升级
- 改造 `utils/llm.py`，支持原生 Tool Calling
- 新增 `call_llm_with_tools` 等封装函数
- 处理 `tool_calls` 的解析与执行逻辑

### 阶段 3：核心节点逐步迁移（最关键）
- **优先**：`data_gathering`（试点，已计划）
- **其次**：`observation`（重点处理 `visual_analyzer`）
- **最后**：`signal_generation`（分阶段拆分与迁移）
  - 先把工具调用部分抽离
  - 再逐步引入 Agent + Tool 执行分离逻辑

### 阶段 4：Graph 结构优化（可选但推荐）
- 评估是否引入 `ToolNode` + 条件边
- 考虑将 `signal_generation` 拆分为：
  - `agent_node`（决策）
  - `tool_execution`（执行）
  - `generate_final_signals`（最终信号生成）
- 提升整体架构的规范性

### 阶段 5：清理与优化
- 逐步删除旧的 Prompt 工具描述
- 统一错误处理和 Mock 机制
- 完善测试覆盖
- 更新文档

## 5. 关键节点迁移优先级

| 优先级 | 节点                  | 改造难度 | 推荐顺序 | 备注 |
|--------|-----------------------|----------|----------|------|
| P0     | `data_gathering`      | 中       | 1        | 最佳试点节点 |
| P1     | `observation`         | 中高     | 2        | 视觉工具为主 |
| P2     | `signal_generation`   | 高       | 3        | 最复杂，需分步 |
| P3     | Graph 整体结构        | 高       | 4        | 引入 ToolNode |

## 6. 技术选型建议

- **工具定义**：统一使用 `@tool`（langchain_core.tools）
- **工具执行**：初期在节点内手动处理，后期可引入 `ToolNode`
- **LLM**：继续使用 `ChatOpenAI(base_url="https://api.x.ai/v1")` + `bind_tools`
- **状态管理**：保持现有 `TAState`，逐步增强
- **开关机制**：环境变量 + State 字段双保险

## 7. 风险与缓解措施

- **Grok Tool Calling 稳定性**：通过试点验证，必要时保留 fallback
- **重构周期过长**：采用小步快跑，每完成一个节点就提交
- **业务功能中断**：严格使用绞杀者模式 + 开关控制
- **Prompt 知识流失**：迁移过程中保留关键 Few-shot 示例

## 8. 预期收益

- 工具调用逻辑更规范、可维护
- 新增工具成本大幅降低
- 多轮工具调用闭环更稳定
- 为未来引入更复杂的 Agent 模式打下基础
- 代码结构更清晰，团队协作更友好

## 9. 下一步行动

1. 完成 `data_gathering` 节点的试点改造（当前优先）
2. 总结试点经验，形成可复用的改造模板
3. 启动 `observation` 节点的改造
4. 制定 `signal_generation` 的分阶段迁移计划

---

**备注**：本路线图为 High Level 版本，具体实施细节以各节点详细计划为准。