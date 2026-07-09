# signal_generation.py 重构计划（详细版，基于真实代码）

## 1. 总体目标

将当前超大 monolithic 的 `signal_generation` 节点逐步拆分，并引入原生 Tool Calling 能力，最终形成清晰的 **Agent → Tool Execution → Signal Generation** 流程。

## 2. 当前代码分析（基于 GitHub 最新代码）

### 主要函数
- `signal_generation(state: TAState) -> TAState`

### 核心问题
1. **Prompt 极度臃肿**：一个 prompt 里混杂了工具描述、Playbook 规则、Few-shot、输出要求、JSON schema 等，超过 100 行。
2. **工具调用是“伪调用”**：prompt 里写了“可用工具列表”，但实际完全靠 LLM 自己输出 JSON，之后手动解析，没有真正的 bind_tools + ToolNode。
3. **视觉信号处理混乱**：先尝试用 observation 里的 visual_signals，如果没有再用 LLM 生成，逻辑分散。
4. **JSON 解析非常脆弱**：大量 try-except + re.search + 默认值，容易在生产环境出问题。
5. **多轮迭代支持差**：虽然有 iteration 字段，但 prompt 里几乎没有真正利用“上一轮信号”进行对比。

## 3. 重构策略：绞杀者模式 + 节点拆分

### 推荐最终架构（长期目标）
```
signal_generation
    ├── agent_node (思考 + 决定是否调用工具)
    ├── tool_execution_node (ToolNode)
    └── generate_signals_node (最终信号生成 + 合并 visual)
```

### 阶段划分（绞杀者模式）

**阶段 1（当前最优先）：工具标准化 + Prompt 瘦身**
- 把 prompt 里列出的 5 个工具真正实现为 `@tool`
- 把工具描述从 prompt 里删除，改用 `bind_tools` 自动注入
- 保留现有 JSON 解析逻辑作为 Legacy

**阶段 2：双路径并存**
- `_signal_generation_legacy`：完全保留当前实现
- `_signal_generation_with_tools`：新路径，使用 bind_tools + 结构化输出

**阶段 3：引入 ToolNode（可选但推荐）**
- 在 graph 中新增 `tool_execution` 节点
- 通过 `add_conditional_edges` 实现 Agent → Tool → Agent 循环

**阶段 4：节点拆分 + 状态机优化**
- 把 signal_generation 拆成 3 个独立节点
- 利用 LangGraph 的 checkpoint + memory 做多轮对比

## 4. 具体实施步骤

### 步骤 1: 把 prompt 里的工具真正实现为 @tool（最高优先级）

把以下 5 个工具从“描述”变成真实可执行的 tool：

```python
@tool
def get_futures_holding(ts_code: str) -> Dict:
    """获取期货持仓排名（主力分析）"""

@tool
def get_futures_basic(exchange: str = "") -> Dict:
    """获取合约基本信息和主力列表"""

@tool
def get_related_futures_dynamic(symbol: str) -> Dict:
    """获取相关品种动态数据"""

@tool
def get_futures_news(symbol: str, limit: int = 5) -> Dict:
    """获取重要新闻/宏观政策"""

@tool
def generate_kline_chart(symbol: str) -> str:
    """生成K线图（返回图片路径或base64）"""
```

### 步骤 2: 实现双路径

保持对外函数名 `signal_generation` 不变：

```python
def signal_generation(state: TAState) -> TAState:
    use_native = os.getenv("USE_NATIVE_TOOL_CALLING", "false").lower() == "true"
    if use_native:
        return _signal_generation_with_tools(state)
    else:
        return _signal_generation_legacy(state)
```

### 步骤 3: 新路径核心逻辑

`_signal_generation_with_tools` 应该：
1. 构建 tools 列表
2. llm_with_tools = llm.bind_tools(tools, tool_choice="auto")
3. response = llm_with_tools.invoke(...)
4. 如果有 tool_calls → 执行工具 → 把结果放回 messages → 再次 invoke
5. 最终要求 LLM 输出结构化 signals JSON
6. 合并 visual_signals（如果 observation 已提供）

### 步骤 4: Prompt 大幅瘦身

新 prompt 只保留：
- 当前 Playbook 规则（通过 manager.build_prompt 注入）
- 输出 JSON schema（严格）
- Few-shot 示例（保留 1-2 个高质量的）
- “视觉信号已由 observation 提供，无需重复分析图像”

把原来 100+ 行的工具描述全部删除。

## 5. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| eaagent/a_plus_plus/nodes/signal_generation.py | 大改 | 实现双路径 + bind_tools 支持 |
| eaagent/a_plus_plus/tools.py | 新增/修改 | 实现 5 个 @tool 函数 |
| eaagent/a_plus_plus/graph.py | 修改 | 可选引入 ToolNode + 条件边 |
| eaagent/a_plus_plus/utils/llm.py | 可选增强 | 支持更 robust 的 tool calling 封装 |

## 6. 风险与缓解措施

| 风险 | 缓解措施 |
|------|----------|
| LLM 工具调用不稳定（Grok） | 先在 tools.py 里做好 fallback + mock 开关 |
| 多轮 tool calling 循环死循环 | 设置 max_iterations + 超时保护 |
| visual_signals 与 LLM 生成信号冲突 | 明确优先级：observation 提供的 visual_signals 优先级最高 |
| JSON schema 漂移 | 使用 Pydantic + with_structured_output（如果 Grok 支持）或严格 prompt + re 解析双保险 |

## 7. 执行顺序建议（务实）

1. **本周优先**：完成 5 个工具的 @tool 实现 + 单测
2. **下周**：实现 `_signal_generation_with_tools` 骨架（先支持 1-2 个工具）
3. **再下周**：把 observation 里的 visual_signals 合并逻辑迁移到新路径
4. **长期**：引入 ToolNode + 条件边，实现真正的 ReAct 风格循环

---

**备注**：signal_generation 是目前整个 Agent 里最复杂、也最需要重构的节点。建议采用“先加测试保护 → 再双路径并存 → 最后逐步替换”的保守策略。