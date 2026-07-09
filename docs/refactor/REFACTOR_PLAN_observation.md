# observation.py 重构计划（详细版，基于真实代码）

## 1. 总体目标

将 `observation.py` 中的 `structured_observation` 节点逐步迁移到更规范的 LangChain/LangGraph 原生工具调用模式，同时保持视觉分析（visual_analyzer）的优先级和缓存机制。

## 2. 当前代码分析（基于 GitHub 最新代码）

### 主要函数
- `structured_observation(state: TAState) -> TAState`
- `_prepare_daily_data(daily_data: List[Dict], max_rows: int = 60) -> str`

### 核心逻辑
1. 从 state 中获取 daily_data
2. 调用 `visual_analyzer`（优先新图像或 force_new）
3. 如果 visual 成功，直接注入 signals 和 obs_data
4. 否则 fallback 到 `call_llm` + JSON 解析
5. 处理 playbook_references 格式
6. 追加到 state["observations"]

### 关键设计点
- visual_analyzer 已经支持缓存（_observation_cache）
- force_new_image 逻辑：is_first_round or has_new_data_requests
- 强调 "视觉优先" 和 "不要重复生成相同12mo图像"

## 3. 重构策略：绞杀者模式 + 工具标准化

### 阶段 1: 工具层标准化（先做）
- 把 `visual_analyzer` 正式注册为 `@tool`
- 暴露给 LLM 的 tool schema 更清晰
- 保留现有缓存和 force_new 参数

### 阶段 2: observation 节点内部双路径
- 保留 `_structured_observation_legacy`
- 新增 `_structured_observation_with_tools`
- 通过环境变量或 state flag 切换

### 阶段 3: Prompt 优化 + Tool Calling 支持
- 把 "工具调用优先" 的逻辑从 prompt 描述改为真正的 bind_tools
- 让 LLM 能主动决定是否调用 visual_analyzer / get_futures_holding 等

### 阶段 4: 节点拆分（可选，长期）
- 把 observation 拆成：
  - visual_analysis_node
  - text_observation_node
  - merge_observation_node

## 4. 具体实施步骤

### 步骤 1: visual_analyzer 改为 @tool
```python
from langchain_core.tools import tool

@tool
def visual_analyzer_tool(
    symbol: str = "RB2610.SHF",
    months: int = 12,
    force_new: bool = False,
    playbook_name: str = "v3"
) -> Dict[str, Any]:
    """视觉K线分析工具（Grok Vision + Playbook）"""
    return visual_analyzer(symbol, months, force_new, playbook_name)
```

### 步骤 2: 在 observation 节点中支持 bind_tools
在 `_structured_observation_with_tools` 中：
- 定义 tools = [visual_analyzer_tool, get_futures_holding, ...]
- llm_with_tools = llm.bind_tools(tools)
- 根据 LLM 返回的 tool_calls 执行对应工具
- 把结果合并进 obs_data

### 步骤 3: 保留视觉缓存逻辑
新路径必须完全兼容现有的 `is_cached_image` 和 force_new 机制。

### 步骤 4: Prompt 清理
逐步移除 prompt 中冗长的 "可用工具列表" 描述，改为让 bind_tools 自动注入 schema。

## 5. 文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| eaagent/a_plus_plus/nodes/observation.py | 修改 | 实现双路径 + 支持 tool calling |
| eaagent/a_plus_plus/tools.py | 修改 | 把 visual_analyzer 包装成 @tool |
| eaagent/a_plus_plus/graph.py | 可选 | 注册新节点或更新导入 |

## 6. 风险与缓解

- **视觉缓存机制破坏**：新路径必须完整保留 _observation_cache 逻辑
- **第一次 round 的 force_new 判断**：需要仔细测试 is_first_round 条件
- **JSON 解析 robustness**：保留现有的 try-except + default JSON

## 7. 测试建议（见 with_test 文件）

优先为以下场景写 UT：
- visual 成功返回 signals
- visual 失败 fallback 到 LLM
- force_new_image 逻辑
- playbook_references 格式标准化

## 8. 执行顺序建议

1. 先完成 tools.py 的 @tool 化（visual_analyzer）
2. 再实现 observation 的双路径骨架
3. 逐步把 tool calling 逻辑补全
4. 最后清理旧 prompt 描述

---

**备注**：本计划与 data_gathering 计划风格一致，强调先加测试保护，再做绞杀者式重构。