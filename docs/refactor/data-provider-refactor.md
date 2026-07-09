# DataProvider 重构进度（2026-06）

## 当前分支
- **分支名**：`refactor/data-provider`
- **状态**：领先远程 7 个 commit（未 push）
- **最后更新**：2026-06-23

## 已完成工作

### 1. 抽象层设计
- 新增 `DataProvider` 抽象基类（`eaagent/data_providers/base.py`）
- 定义统一接口：`get_daily()`、`get_minute()`、`get_symbol_info()`

### 2. 数据源实现
- `TushareFuturesProvider`：已完成 + 单元测试
- `TushareStockProvider`：已完成 + 单元测试
- `AkshareStockProvider`：已完成（但目前获取数据不稳定，返回空数据）

### 3. Factory 模式
- 新增 `get_data_provider()` 工厂方法
- 支持通过字符串切换数据源（`tushare_futures`、`tushare_stock`、`akshare_stock`）

### 4. Harness 集成
- 在 `data_ingestion` 节点中接入新 DataProvider 体系
- 支持 Mock 模式与真实模式切换（通过 `USE_MOCK_OBSERVATION` 环境变量）
- 已实现多时间框架数据提取（日线 + 分钟线），并转为结构化特征存入 state

### 5. 测试
- 核心单元测试已通过（Tushare 相关）
- Akshare 相关测试已修复 mock 问题

## 当前问题

- **AkshareStockProvider** 获取数据不稳定
  - 即使使用固定历史日期，仍然返回 0 条数据
  - 可能原因：Akshare 接口参数、`adjust` 参数、或对部分股票支持不稳定
- 目前股票分析主要依赖 Tushare，Akshare 尚未真正跑通

## 下一步计划

| 优先级 | 任务 | 说明 | 状态 |
|--------|------|------|------|
| 高 | 修复/优化 AkshareStockProvider | 让 Akshare 能稳定返回数据 | 进行中 |
| 中 | 完善多时间框架特征提取 | 让 30min、5min 数据更可靠地被使用 | 待做 |
| 中 | 更新 README | 记录 DataProvider 重构成果 | 待做 |
| 低 | 清理旧代码 | 逐步减少对旧 `get_market_data` 的依赖 | 待做 |

## 关键文件变更

- `eaagent/data_providers/`
  - `base.py`
  - `tushare_futures.py`
  - `tushare_stock.py`
  - `akshare_stock.py`
  - `factory.py`
- `eaagent/a_plus_plus/nodes/data_ingestion.py`
- `tests/unit/test_akshare_stock_provider.py`
- `tests/unit/test_data_provider_factory.py`

## 总结

目前已完成 **DataProvider 抽象层 + 多数据源支持 + Harness 初步集成** 的核心框架搭建。Tushare 相关功能已基本可用，Akshare 作为免费备选数据源仍在调试中。

整体重构方向正确，架构具备较好的扩展性（未来可轻松接入聚宽、米筐等数据源）。
