# Plan: 参考Grok Share链接实现EA Agent架构演进 (Harness + Playbook规则引擎 + 多时间框架仲裁)

## Context (背景)
用户提供两个 Grok Share 链接：
- 原链接 (https://grok.com/share/c2hhcmQtNA_13ade8a3-e235-40af-bf03-2da72e00c02e)：**EA Agent中长期演进大计划**（Martin Fowler Agent Harness落地、Playbook规则引擎、多时间框架仲裁、6 Phase路线图）。
- 新链接 (https://grok.com/share/c2hhcmQtNA_da56a84d-39de-4873-962f-d51d23e6c66f)：**本次聊天的布局**（Web UI/报告布局参考：实时 streaming 日志 + prompt blocks、rich Markdown Blog 风格、50% 宽度 resizable panels、Tabs 相关 K 线、Chinese 菜单、incremental live updates）。

当前项目状态：
- **Phase 0 (Web/UI)**: **100% 完成** — 中文主力合约菜单 (螺纹钢 RB2610.SHF 等)、50% 宽度富文本 Blog 报告 (多轮总结/关键规则/决策依据/News+Holding+LLM 洞察)、独立 Tabs 相关 K 线、Strategy 切换、prompt 捕获、动态 RELATED_MAP、强制多轮 (MAX_ROUNDS=5)、LLM 工具调用 (5 tools with schemas)。
- **Phase 1 (Harness 骨架)**: **0%** — 待启动 (SteeringNode + structured AnalysisState + RulesEngine)。
- 最新状态: git clean (c8d16f3 cleanup test stub + report tweaks), all explicit requests done, tests pass.
- 符合AGENTS.md (Test-First、minimal、reuse、incremental commit/push、中文回复、无新文件优先、Orient-Clarify-Slice-Check-TDD-Verify-Reflect)。

此plan 已更新当前进度（Phase 0 100% 完成，Phase 1 待启动）。**Phase 3 “杀手级”功能已启动并完成第一步**（来自最新 Share 链接）：
- **Streamlit Dashboard**：3栏布局骨架完成 (左侧栏品种/策略/Playbook + 主Tabs多轮轨迹/K线/报告/回测 + 右侧栏 State/干预/日志)，复用 report_builder/kline/graph。
- **backtest/engine.py**：VectorBT 最小回测引擎 (单品种资金曲线 + 指标)。
- **报告增强**：Mermaid 决策路径 + Critique 柱状图 (真实 LLM score/rules 解析，非 fake)。
- **Test-First**：test_backtest.py + test_dashboard.py (结构验证通过)。
- **依赖**：streamlit/vectorbt/pyarrow/jsonschema 安装成功 (numba/llvmlite 构建问题暂用 pandas 模拟，建议 conda 环境解决)。

**用户指令 "直接进入Phase3"** 已执行。当前进度 40% (Dashboard 骨架 + 报告真实数据 + 测试)。下一步：graph 持久化/人工钩子 + evaluation A/B + 完整 VectorBT + Java 骨架。保持 Web 稳定。

## Recommended Approach (推荐方案)
采用Share链接的**6 Phase路线图**，优先**Phase 1**（Harness组件 + LangGraph重构 + 可观测性），然后Phase 2 (Playbook结构化规则引擎)。 

**新增 Phase 3 “杀手级”功能**（来自最新 Share 链接，强烈推荐实现）：
- **backtest/**：完整回测引擎（VectorBT），支持单品种 & 多品种批量，输出资金曲线 + 全套指标 (Sharpe, MaxDD, WinRate 等)。
- **evaluation/**：A/B 测试（Agent vs 纯规则）、样本内外验证、交叉验证。
- **Streamlit Dashboard** 主入口（推荐替换或并存 app.py）：**推荐 3 栏布局**。
  - **左栏 (侧边栏)**：品种选择（下拉：螺纹钢 RB、铁矿 I、纯碱 SA...）、策略模式 (Full/Core/IdOnly)、Playbook 版本选择、“开始分析”按钮 + “模拟实盘”开关。
  - **主内容区 (Tabs)**：
    - 多轮分析轨迹：时间轴 (第1-5轮)，每轮展开 (输入数据 → Playbook 规则 → LLM 思考 → Critique 评分) + 工具调用记录表格。
    - K线 + 可视化：动态 Plotly K 线 + 信号标注 + 持仓建议。
    - 最终报告：结构化卡片 (看多/看空/中性 + 置信度)、风险提示 + 建议仓位、一键导出 PDF/Markdown。
    - 绩效回测 Tab：资金曲线图、指标表格、A/B 测试对比。
  - **右栏 (固定)**：当前 Shared State 概览 (轮次、总分数)、“人工干预”输入框 + “强制结束”按钮、日志窗口 (实时 Graph 执行过程)。
- **Java 版本入口**（可选但强烈推荐）：新建 `java_agent/` 文件夹，放置 LangChain4j + LangGraph4j 骨架代码。
- **生产化**：FastAPI 后端接口 + Docker 支持。

**Phase 2 增强已有功能**（与 Phase 3 并行）：
- graph.py：增加 thread_id 持久化、支持中途人工介入钩子、把 Critique 评分加入 State。
- 报告增强：在现有富文本报告中增加“决策路径 Mermaid 图” + “Critique 各轮评分柱状图”。
- Playbook 增强：支持版本切换 + 规则命中高亮 + 引用计数。
- UI 增强：增加“切换 Mock/实盘”按钮 + “导出完整 JSON 日志”按钮。

- **Harness**：Guides (Playbook YAML/Pydantic)、Sensors (Tushare data_provider)、Actor (ReAct/signal_gen)、Steering (冲突仲裁 + 风险)、Memory (state + trace)。
- **Playbook**：从markdown → 结构化规则集 (id, timeframe, condition, action, priority)，RulesEngine节点逐条验证。
- **多时间框架 (Phase 3 核心)**：子图/并行节点聚合共识，SteeringNode强制“一致才交易”（日线未确认或多框架冲突 → NO_TRADE；输出 TimeframeConsensus 包含趋势/形态/信号强度/冲突标记；TimeframeAnalysis Pydantic 模型）。
- **风险内嵌 (Phase 4)**：SteeringNode 内建风险评估 (止损、30%仓位、R:R)、RiskCalculationTool，决策必须包含 risk_assessment。
- **工具体系 (Phase 5)**：ToolRegistry (分类 + Steering 约束)、工具调用可观测性 (参数/返回/耗时)。
- **评估与记忆 (Phase 6)**：PostDecisionReview 节点、分层 Memory (短期轨迹 + 长期规则执行历史)、质量评分 (Playbook遵循率、冲突拦截率)。
- **Web/UI (Phase 0)**：已作为快速验证完成（**采用新 Share 链接的聊天布局**：实时 streaming 日志 + prompt blocks、rich Markdown Blog 风格、多轮 incremental live updates、50% 宽度 resizable panels、独立 Tabs 相关 K 线、Chinese 主力合约菜单 + Strategy 下拉、prompt 完整捕获）。
- **Test-First**：每个Phase先写integration/unit test (test_harness.py, test_rules_engine.py, test_backtest.py, test_dashboard.py)，复用现有graph.py/state.py/tools.py + report_builder + kline。
- **No gold-plating**：最小变更，先落地 Streamlit Dashboard 3栏主入口 (使用现有 Gradio 报告/K线 + Streamlit 组件)，backtest VectorBT 最小引擎 (单品种资金曲线)，然后扩展 evaluation/A/B 和 Java 骨架。复用现有 critique_result、final_output、Mermaid 支持。

避免循环导入、保持generator yield兼容、确保prompt捕获和50%宽度报告不回归。

## Critical Files (关键文件) - 包含 Phase 3 新功能 (直接进入Phase3)
- `streamlit_dashboard.py` (**主入口** - 3栏布局：左侧栏品种/策略/Playbook + 主Tabs (多轮轨迹时间轴/K线可视化/最终报告/绩效回测) + 右侧栏 Shared State/人工干预/实时日志)。
- `backtest/engine.py` (VectorBT 回测引擎 - 单/多品种批量、资金曲线 + Sharpe/MaxDD/WinRate 等全套指标)。
- `evaluation/ab_test.py` (A/B 测试 Agent vs 纯规则 + 样本内外验证)。
- `eaagent/a_plus_plus/graph.py` (增强：thread_id 持久化、人工介入钩子、Critique 评分入 State)。
- `web/report_builder.py` (增强：添加 Mermaid 决策路径图 + Critique 各轮评分柱状图 (Plotly))。
- `eaagent/a_plus_plus/state.py` (扩展 critique_scores + multi_timeframe_analysis)。
- `eaagent/a_plus_plus/nodes/steering.py` (增强人工介入 + 风险)。
- `java_agent/main.java` (LangGraph4j 骨架 - 可选)。
- `docker/Dockerfile` + `api/main.py` (FastAPI 生产接口)。
- `tests/integration/test_backtest.py + test_dashboard.py` (Test-First)。
- `docs/wiki/Streamlit-Dashboard-Layout.md` (3栏布局图 + Mermaid 示例)。
- 现有 `web/app_graph.py + web/report_builder.py + eaagent/a_plus_plus/*` (复用 kline、report、graph)。

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
1. **Orient & Clarify**：阅读**两个 Share 链接**（长期 Harness 计划 + 本次聊天布局参考） + 当前代码 (graph.py, state.py, observation.py, report_builder.py, AGENTS.md, todo/remaining_work.md)。确认 Harness 组件边界、Playbook 结构 (YAML vs JSON) 和 UI 布局一致性。
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

Plan reviewed and updated: **Phase 3 “杀手级”功能进度 40%** (Dashboard 3栏骨架 + 真实 critique 评分/规则 (非 fake) + VectorBT 最小回测 + Mermaid/柱状图报告 + Test-First tests)。依赖 (numba/llvmlite) 构建问题暂用 pandas 模拟 (conda 环境推荐)。覆盖两个 Share 链接核心 (长期 6 Phase + 本次聊天布局)、精确文件/行号复用、Test-First。**按照原计划继续** (graph 持久化/人工钩子 + evaluation A/B + 完整 VectorBT)。已就绪，下一步实施。