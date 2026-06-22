# Data Provider Refactor - Detailed Todo (XP + TDD Style)

> 使用 XP 思想进行小步增量开发，优先使用 TDD（Test First）。
> 每个 Task 都应该是可独立验证的小增量。

**目标**：实现 `DataProvider` 抽象层，支持期货和股票数据获取。

---

## Phase 1: 基础抽象层建立（小步、快速反馈）

### Task 1.1: 定义 DataProvider 抽象基类
- [ ] 创建 `eaagent/data_providers/base.py`
- [ ] 定义抽象方法：`get_daily()`、`get_minute()`
- [ ] 写单元测试 `tests/unit/test_data_provider_base.py` （测试接口定义）

### Task 1.2: 实现 TushareFuturesProvider（迁移现有逻辑）
- [ ] 创建 `eaagent/data_providers/tushare_futures.py`
- [ ] 实现 `get_daily()` 和 `get_minute()`
- [ ] 写集成测试 `tests/integration/test_tushare_futures_provider.py`

### Task 1.3: 创建 DataProviderFactory
- [ ] 创建 `eaagent/data_providers/factory.py`
- [ ] 支持通过字符串创建 `tushare_futures` Provider
- [ ] 写单元测试验证工厂方法

## Phase 2: 支持股票 API（适配器模式）

### Task 2.1: 实现 TushareStockProvider
- [ ] 创建 `eaagent/data_providers/tushare_stock.py`
- [ ] 实现 `get_daily()` 和 `get_minute()`（适配 Tushare 股票接口）
- [ ] 写集成测试 `tests/integration/test_tushare_stock_provider.py`

### Task 2.2: 扩展 Factory 支持股票
- [ ] 修改 Factory 支持 `tushare_stock`
- [ ] 添加单元测试验证股票 Provider 创建

## Phase 3: Harness 集成

### Task 3.1: 在 graph.py 中使用 Factory
- [ ] 修改 `eaagent/a_plus_plus/graph.py`，通过 Factory 获取 DataProvider
- [ ] 写集成测试验证数据源切换

### Task 3.2: 更新现有工具调用
- [ ] 将 `tools/tushare_*.py` 中的逻辑逐步迁移到 Provider
- [ ] 保持原有接口兼容性（避免破坏现有代码）

## Phase 4: 测试与文档

### Task 4.1: 完善测试覆盖
- [ ] 为新的 Provider 补充单元测试和集成测试
- [ ] 更新 CI 覆盖率报告

### Task 4.2: 更新文档
- [ ] 更新 `docs/AGENTS.md`
- [ ] 创建 ADR 记录此次重构决策
- [ ] 更新 `todo/remaining_work.md`

---

## XP/TDD 开发节奏建议

- 每个 Task 都尽量控制在 1-2 小时可完成
- 优先写测试，再实现功能
- 每完成一个 Phase 后运行全量测试并提交
- 小步提交 + 快速反馈

**最后更新**：2026-06-22