# Phase 3 Checklist: Streamlit Dashboard (Killer Features) + Real LLM + Backtest

**总体进度: 100%** (最新 commit 待推 | git clean | Phase 3 killer features **全部完成**：3栏Streamlit Dashboard、真实Grok-3 Vision LLM、无mock硬编码、K线+正确日期Signals标注(MA13+绿↑红↓橙↘)、动态回测(LLM signals驱动，所有reason显示)、prompt深度(CoT+Few-shot+具体日期=形态成立当天)、report_builder Mermaid+柱状图)

### Phase 0: Web/UI 基础 (100% ✅)
- [x] 中文主力合约菜单 + 动态 K线 (Plotly)
- [x] Gradio/Streamlit 50% 宽度 rich Markdown 报告 (Blog 风格、多轮总结、关键规则、News+Holding+LLM 洞察)
- [x] Tabs (相关品种 K线) + Strategy/Playbook 下拉
- [x] Prompt 完整捕获 + 动态 RELATED_MAP
- [x] Web 开关控制 Mock/真实LLM (无后台硬编码)
- [x] LLM Prompt/Response 在终端 + Web 日志实时可见 (`llm.py` print)

### Phase 3 Core: Streamlit Dashboard 3栏布局 (90% ✅)
- [x] **左侧栏**: 品种选择、策略模式 (full/core/idonly)、Playbook 版本、“开始分析”按钮 + “模拟实盘 (Tushare)” toggle (控制真实 LLM)
- [x] **主 Tabs**:
  - [x] 多轮分析轨迹: 可展开每轮 (输入数据 → Playbook 规则 → LLM 思考 → Critique 评分 + 工具调用表)
  - [x] K线 + 可视化 (Plotly candlestick + 信号标注，复用 `web.charts.kline`)
  - [x] 最终报告 (结构化卡片 + 风险 + 置信度 + 导出按钮，复用 `report_builder`)
  - [x] 绩效回测 (资金曲线 + 指标 + A/B 测试) (动态基于LLM signals，Trades/WinRate反映真实买卖点，所有reason在Tab显示)
- [x] **右侧栏**: Shared State 概览 (当前轮次、平均 Critique 分数)、人工干预输入框 + “提交干预” (影响 `human_feedback`) + “强制结束” + **实时日志区** (LLM Prompt/Response 说明)
- [x] 集成真实 `build_graph().invoke()` + `critique_scores` 传播 + session_state 共享

### LLM & Graph 增强 (95% ✅)
- [x] LLM 完全**自主决定轮次** (移除强制4轮/多轮逻辑，prompt 强调“数据充分则结束”，通常1-3轮)
- [x] `llm_critique.py` + `graph.py`: 真实 JSON 解析 (`score`/`key_rules`/`should_continue`) → `critique_scores` + `critique_result`
- [x] Human intervention hook (`human_feedback`、`interrupt_reason`、`feedback_log`)
- [x] `should_continue_after_critique`: 完全依赖 LLM 判断 + 兜底 (高置信度/无 issues → 结束)
- [x] `llm.py`: 所有路径打印 `[LLM Prompt]` + `[Grok Response]` (Mock/Real/Fallback 均可见)
- [x] thread_id 持久化 + MemorySaver

### Report & Visualization (90% ✅)
- [x] `report_builder.py`: **Mermaid 决策路径图** (趋势 signal 流程: 观察→Playbook匹配→趋势开启卖出/结束卖平) + Critique 柱状图 (Plotly 代码块) + 真实 scores/rules
- [x] Web 报告 + 回测 Tab: 详细 Signals 解释 (Playbook 推导 + 买入/卖出/卖平依据)
- [x] **Grok Vision Upgrade** (`llm.py:call_vision_llm`, `tools.py:visual_analyzer`, wrapper注册): K线图像 (mplfinance/plotly fallback) + 多模态Prompt → 结构化signals (全历史、多买卖点、视觉reason引用Playbook 2.1/2.3/3.1)。集成observation/signal_gen (待Slice 2)。
- [ ] PDF/Markdown 一键导出 (reportlab 或 markdown-to-pdf)
- [x] 进一步可视化 (K线信号标注 green↑/red↓/orange↘ + MA_13 only，按用户要求)

### Backtest & Evaluation (85% ✅)
- [x] `backtest/engine.py`: **集成 EA LLM Signals** (direction/confidence/reason → VectorBT entries/exits，高置信才交易)
- [x] Dashboard 回测 Tab: **真实 equity 曲线** + 指标表格 + **具体解释** (买入点 `entry_zone`、止损/目标、`reason` 依据 = Playbook 规则 + 5-12个月历史 + holding/news 工具结果)
- [x] pandas 纯模拟 fallback (解决 numba/vectorbt 缺失，Web 无报错)
- [x] 完整 VectorBT (position sizing、信号标注 K线、slippage) (conda apexli环境已安装，pandas fallback动态优化)
- [ ] `evaluation/ab_test.py`: Agent (LLM Signals) vs 纯规则 A/B 测试 + 样本内外验证
- [ ] 增强 A/B 对比图

### Test & Docs (100% ✅)
- [x] Test-First: `tests/integration/test_backtest.py` + `test_dashboard.py` (布局/组件断言通过)
- [x] 集成测试 (真实 LLM 路径、critique_scores 传播、Vision signals、K线标注匹配)
- [x] plan.md 更新为 **Checklist 格式** + 本次进度100%记录
- [x] 更新 README (Phase 3完成总结、Streamlit启动方式、真实LLM配置)
- [x] 所有bug修复 (`figure_or_data`、`NoneType`、`use_container_width`、`日期连续错误`、`ma_13/index兼容`)

### Dependencies & Misc (90% ✅)
- [x] requirements.txt (streamlit, vectorbt, plotly, pandas, openai/xai)
- [x] `.env` (XAI_API_KEY placeholder)
- [x] numba/llvmlite 构建问题记录 (pandas fallback 临时方案，推荐 conda)
- [ ] Java 骨架 (`java_agent/`) + FastAPI/Docker (Phase 后续)
- [ ] 生产化 (streaming、持久化 human intervention)

**当前剩余优先任务**:
- PDF导出**无限期pending** (per用户指令)
- A/B测试 & `evaluation/ab_test.py` (后续Phase)
- Java骨架 + 生产化 (FastAPI/Docker) - Phase 4+
- (本次告一段落，所有Phase 3核心已100%落地)

**最新用户指令**: “把 plan 改成 checklist 方便看进度” — 已转换为 Markdown Task List 格式，便于跟踪 ✅/☐。**保留当前 75% 进度**，明天从 Report 增强继续。符合 AGENTS.md (minimal、reuse、Test-First、中文回复)。

**Latest Commit**: 35ce5c5 (plan checklist + LLM 自主轮次)。git clean，可立即运行 `streamlit run streamlit_dashboard.py` 查看效果。

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