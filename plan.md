# Plan: 参考Grok Share链接实现EA Agent架构演进 (Harness + Playbook规则引擎 + 多时间框架仲裁)

## Context (背景)
用户提供Grok Share链接 (https://grok.com/share/c2hhcmQtNA_13ade8a3-e235-40af-bf03-2da72e00c02e)，内容为**EA Agent中长期演进大计划**（Martin Fowler Agent Harness落地、Playbook从Prompt背景→可执行规则引擎、多时间框架协同+冲突仲裁、风险内嵌、ToolRegistry、分阶段6 Phase路线图）。当前项目状态：
- **Phase 0 (Web/UI)**: **100% 完成** — 中文主力合约菜单 (螺纹钢 RB2610.SHF 等)、50% 宽度富文本 Blog 报告 (多轮总结/关键规则/决策依据/News+Holding+LLM 洞察)、独立 Tabs 相关 K 线、Strategy 切换、prompt 捕获、动态 RELATED_MAP、强制多轮 (MAX_ROUNDS=5)、LLM 工具调用 (5 tools with schemas)。
- **Phase 1 (Harness 骨架)**: **0%** — 待启动 (SteeringNode + structured AnalysisState + RulesEngine)。
- 最新状态: git clean (c8d16f3 cleanup test stub + report tweaks), all explicit requests done, tests pass.
- 符合AGENTS.md (Test-First、minimal、reuse、incremental commit/push、中文回复、无新文件优先、Orient-Clarify-Slice-Check-TDD-Verify-Reflect)。

此plan 已更新当前进度（Phase 0 100% 完成，Phase 1 待启动）。以Share链接为核心，**下一步启动 Phase 1 (Harness骨架 + SteeringNode)**，同时保持 Web 稳定。

## Recommended Approach (推荐方案)
采用Share链接的**6 Phase路线图**，优先**Phase 1**（Harness组件 + LangGraph重构 + 可观测性），然后Phase 2 (Playbook结构化规则引擎)。 
- **Harness**：Guides (Playbook YAML/Pydantic)、Sensors (Tushare data_provider)、Actor (ReAct/signal_gen)、Steering (冲突仲裁 + 风险)、Memory (state + trace)。
- **Playbook**：从markdown → 结构化规则集 (id, timeframe, condition, action, priority)，RulesEngine节点逐条验证。
- **多时间框架**：子图/并行节点聚合共识，SteeringNode强制“一致才交易”。
- **Web/UI (Phase 0)**：已作为快速验证完成（中文菜单 + 50% 宽度富文本报告 + Tabs K线 + Strategy 切换 + prompt 日志）。
- **Test-First**：每个Phase先写integration/unit test (test_harness.py, test_rules_engine.py)，复用现有graph.py/state.py/tools.py。
- **No gold-plating**：最小变更，先落地SteeringNode + structured Playbook，再扩展。

避免循环导入、保持generator yield兼容、确保prompt捕获和50%宽度报告不回归。

## Critical Files (关键文件)
- `eaagent/a_plus_plus/state.py` (新AnalysisState + TimeframeAnalysis + DecisionTrace)。
- `eaagent/a_plus_plus/nodes/steering.py` (新SteeringNode：冲突仲裁、风险评估、规则检查)。
- `eaagent/a_plus_plus/graph.py:100-400` (添加Steering节点、conditional edges、subgraph支持)。
- `eaagent/prompts/fortress.py + playbooks/manager.py` (结构化加载YAML规则)。
- `eaagent/a_plus_plus/rules_engine.py` (新RulesEngine，可复用现有quality_sensor)。
- `web/app_graph.py + web/report_builder.py` (Phase 0：确保prompt/多轮报告稳定，添加Harness trace显示)。
- `tests/integration/test_harness.py + test_rules_engine.py` (Test-First)。
- `docs/wiki/Harness-Overview.md + README.md + todo/remaining_work.md` (文档更新)。

## Existing Functions/Utilities to Reuse (带文件:行号)
- `eaagent/a_plus_plus/graph.py:105-350` (现有nodes: observation, data_gathering, signal_generation, quality_sensor, llm_critique, final_output；复用conditional edges + should_continue)。
- `eaagent/a_plus_plus/nodes/observation.py:18-110` (structured_observation + data_requests + prompt捕获)。
- `eaagent/a_plus_plus/tools.py:262-400` (get_futures_holding, get_related_futures_dynamic, get_futures_news — 扩展为Sensors)。
- `eaagent/a_plus_plus/state.py` (TAState — 扩展为AnalysisState)。
- `web/app_graph.py:17-62` (run_analysis generator + full_log + extract_ts_code + 50%宽度Row)。
- `eaagent/playbooks/manager.py` (load + build_prompt — 升级为load_rules_yaml)。
- `tests/integration/test_futures_apis.py + test_graph_integration.py` (复用Tushare/Web测试框架)。
- AGENTS.md (Test-First流程、minimal、Chinese responses)。

## Implementation Steps (5-phase workflow)
1. **Orient & Clarify**：阅读Share链接 + 当前代码 (graph.py, state.py, observation.py, report_builder.py, AGENTS.md, todo/remaining_work.md)。确认Harness组件边界和Playbook结构 (YAML vs JSON)。
2. **Slice**：Phase 0 (Web稳定验证) + Phase 1 (SteeringNode + basic Harness) 为第一slice。后续Phase 2 (RulesEngine + structured Playbook)。
3. **Check**：运行现有test (test_kline_chart, test_futures_apis, test_graph_integration)，确认Web按钮、prompt捕获、多轮报告、K线正常。
4. **TDD**：先写test_harness.py (SteeringNode输入输出)、test_rules_engine.py (规则验证)。然后实现state.py更新、steering.py、graph.py集成。
5. **Verify & Reflect**：运行Web (python -m web.app_graph)，验证多轮分析含Steering输出、规则引用、冲突仲裁。更新README/Mermaid图。Reflect：是否符合“严格纪律驱动” (无冲突不交易)。Incremental commit/push ("feat(harness): Phase 1 - SteeringNode + structured state")。

## Verification (验证)
- **Unit/Integration**：`pytest tests/integration/test_harness.py -q --tb=no` 和 `test_rules_engine.py` — 断言SteeringNode输出consensus、rules_passed、risk_assessment、no_trade_if_conflict。
- **Web/E2E**：`python -m web.app_graph`，选择RB2610.SHF，验证报告含“多轮分析路径总结”、“关键引用规则一览”、“最终决策依据”、“Steering仲裁结果”、Prompt可见、K线/Tabs正常、无N/A。
- **Manual**：grep "SteeringNode|RulesEngine|TimeframeConsensus|DecisionTrace"，运行完整EA分析确认“一致才交易”逻辑。
- **Docs**：README添加Harness Mermaid图 + Phase进度，更新todo/remaining_work.md。
- 符合AGENTS.md (Test-First、无gold-plating、reuse现有graph/nodes/tools、incremental commit、Chinese response)。

Plan reviewed and complete. 覆盖Share链接核心 (Harness + Rules + Multi-timeframe + Risk)、当前Web状态、精确文件/行号复用、5-phase步骤、详细验证。已就绪，可执行 (从Phase 0/1开始)。