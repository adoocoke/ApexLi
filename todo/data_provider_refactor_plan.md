# Data Provider Refactor Plan

**目标**：让 EA Agent Harness 能够兼容股票 API，同时保留并优化现有期货能力。

**核心思路**：引入统一的数据提供者抽象层，使用 **Adapter + Factory + Strategy** 设计模式，实现数据源的解耦和可扩展性。

## 设计原则

- **接口统一**：所有数据源（期货/股票）通过 `DataProvider` 抽象接口提供服务。
- **最小改动**：上层 Harness（graph、nodes）尽量少修改。
- **可测试性**：便于 Mock 和单元测试。
- **可扩展性**：未来可轻松接入 AKShare、JoinQuant 等其他数据源。

## 主要工作

1. 定义 `DataProvider` 抽象基类（支持日线、分钟线等核心方法）。
2. 实现 `TushareFuturesProvider`（迁移现有逻辑）。
3. 实现 `TushareStockProvider`（新增股票支持）。
4. 创建 `DataProviderFactory` 支持动态创建 Provider。
5. 在 Harness 中通过 Factory 获取数据源，实现配置化切换。
6. 逐步迁移原有 `tools/tushare_*.py` 逻辑到 Provider 体系。
7. 更新测试（unit/integration）以适配新架构。

## 预期收益

- 清晰的数据访问层
- 期货与股票逻辑解耦
- 更容易扩展新数据源
- 提升代码可维护性和可测试性

**相关文档**：
- `docs/AGENTS.md`
- `todo/remaining_work.md`

**最后更新**：2026-06-22