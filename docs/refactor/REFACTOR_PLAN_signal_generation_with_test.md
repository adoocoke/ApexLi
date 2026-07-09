# signal_generation.py 单元测试补充计划（详细版）

## 1. 当前测试覆盖情况

`signal_generation.py` 目前**几乎没有单元测试**。这是整个重构计划里风险最高的部分，必须优先补测。

## 2. 需要测试的核心函数 / 逻辑

| 模块 | 优先级 | 复杂度 | 测试重点 |
|------|--------|--------|----------|
| `signal_generation` 主流程 | P0 | 极高 | Legacy 路径完整性、visual_signals 合并、JSON 解析 |
| `_signal_generation_legacy` | P0 | 高 | 完全保留原有行为 |
| `_signal_generation_with_tools` | P0 | 高 | 新路径的 tool calling 流程 |
| JSON 解析 + fallback 逻辑 | P0 | 中 | 各种异常输入下的鲁棒性 |
| visual_signals 优先合并逻辑 | P1 | 中 | observation 提供 vs LLM 新生成 |

## 3. 推荐测试文件

`tests/nodes/test_signal_generation.py`

## 4. 核心测试场景（必须覆盖）

### 4.1 Legacy 路径测试（重构前必须通过）

**TC-SIG-001: 正常 LLM 返回有效 JSON**
- Mock call_llm 返回包含 "signals" 的 JSON 字符串
- 验证 state["signals"] 被 append
- 验证 confidence 被更新

**TC-SIG-002: LLM 返回非 JSON（触发 re.search）**
- Mock call_llm 返回带 ```json ... ``` 的字符串
- 验证能正确提取 JSON

**TC-SIG-003: LLM 返回完全无法解析的内容**
- Mock call_llm 返回纯文本
- 验证使用默认 signal_data（direction="观望"）

**TC-SIG-004: observation 已有 visual_signals**
- state["observations"][-1] 包含 "visual_signals"
- 验证优先使用 visual_signals，而不是重新调用 LLM

**TC-SIG-005: 多轮迭代（iteration > 1）**
- 验证 prompt 中 iteration 信息被正确注入（未来增强点）

### 4.2 新路径（_signal_generation_with_tools）测试

**TC-SIG-006: 工具调用流程**
- Mock llm_with_tools 返回 AIMessage with tool_calls
- 验证对应 tool 被执行
- 验证 tool 结果被放回 messages 并再次调用 LLM

**TC-SIG-007: 无需工具，直接输出 signals**
- LLM 直接返回结构化 signals（无 tool_calls）
- 验证流程结束

**TC-SIG-008: 工具调用 + visual_signals 合并**
- 同时存在 tool 返回结果 和 observation visual_signals
- 验证合并逻辑正确（优先级、去重等）

### 4.3 异常与边界测试

**TC-SIG-009: call_llm 抛出异常**
- 验证使用默认观望信号 + 记录错误

**TC-SIG-010: state 中缺少必要字段**
- observations 为空
- 验证能优雅降级

**TC-SIG-011: signals 字段格式漂移**
- LLM 返回的 signal 缺少某些字段
- 验证使用默认值补全

## 5. Mock 清单

需要 mock 的主要对象：
- `eaagent.a_plus_plus.utils.llm.call_llm`
- `eaagent.playbooks.manager`（build_prompt）
- `langchain_core.language_models.chat_models.BaseChatModel`（bind_tools 返回的 llm_with_tools）

## 6. 测试执行顺序建议（务实）

**第一批（本周必须完成，保护 Legacy）**：
- TC-SIG-001 ~ 005（Legacy 路径）

**第二批（重构中同步补充）**：
- TC-SIG-006 ~ 008（新路径核心流程）

**第三批（重构后）**：
- TC-SIG-009 ~ 011（异常与边界）
- 增加对多轮迭代、tool calling 循环的压力测试

## 7. 与重构的配合策略

1. **重构前**：Legacy 路径所有核心测试必须通过
2. **重构中**：新路径每实现一个子流程，就立刻补对应测试
3. **重构后**：可以用同一套测试对比新旧路径的输出差异
4. **长期**：引入 property-based testing（Hypothesis）测试 JSON schema 的各种变体

## 8. 覆盖率目标

- 重构前：Legacy 路径 ≥ 75% line coverage
- 重构完成后：整体 ≥ 85%，关键路径（JSON 解析、visual 合并、tool calling）100% 分支覆盖

---

**重要提醒**：signal_generation 是目前代码里最脆弱、也最核心的节点。**先把 Legacy 测试补全，再动任何重构代码**，这是最低限度的风险控制。