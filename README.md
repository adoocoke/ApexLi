# EA Agent

**EA Agent** 是一个基于 **LangGraph** 构建的**期货/股票技术分析智能体**，核心目标是实现**透明、可观测、可迭代**的多轮技术分析流程。

项目采用 **Martin Fowler Agent Harness** 思想，结合 **DataProvider + Factory** 架构和结构化 LLM 输出，打造可控的分析闭环。

---

## 核心特性

| 特性                    | 说明 |
|-------------------------|------|
| **DataProvider 架构**   | 统一抽象层，支持期货（TushareFuturesProvider）和股票（TushareStockProvider） |
| **Factory 模式**        | 通过 `get_data_provider(name)` 统一创建 Provider |
| **多时间框架支持**      | 日线 + 30分钟 + 5分钟数据获取（data_ingestion 节点） |
| **多轮自动分析**        | 支持最多 5 轮自动迭代分析 |
| **Playbook Strategy**   | 支持 `Full` / `Core` / `IdOnly` 三种 Playbook 注入策略 |
| **结构化 LLM 输出**     | 观察和信号节点均输出 JSON |
| **Mock / 真实数据**     | 通过 `USE_MOCK_OBSERVATION` 快速切换 |
| **完整测试覆盖**        | pytest + Makefile 管理测试 |

---

## 快速开始

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
pip install -e ".[dev,langgraph,tushare]"
```

### 环境准备
```bash
export TUSHARE_TOKEN=your_token_here
```

### 运行期货分析（Mock 模式）
```bash
python -m eaagent.a_plus_plus.graph
```

### 运行股票分析（真实 Tushare）
```bash
USE_MOCK_OBSERVATION=false python -c "
from eaagent.a_plus_plus.graph import create_initial_state, build_graph
app = build_graph()
state = create_initial_state('000001.SZ')
config = {'configurable': {'thread_id': state['thread_id']}}
app.invoke(state, config)
"
```

### 运行测试
```bash
make test
make test-cov
```

---

## 项目结构

```
eaagent/
├── eaagent/
│   ├── data_providers/              # 新 DataProvider 架构
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── tushare_futures.py
│   │   └── tushare_stock.py
│   ├── a_plus_plus/
│   │   ├── graph.py
│   │   ├── nodes/
│   │   │   └── data_ingestion.py   # 集成新 Provider
│   │   └── ...
├── tests/
│   └── unit/
│       ├── test_tushare_stock_provider.py
│       └── test_data_provider_factory.py
└── README.md
```

---

## 主要设计亮点

### 1. Playbook Strategy Pattern
支持三种注入方式：
- `full`：发送完整 Playbook（默认）
- `core`：仅发送精简核心规则（节省 Token）
- `id_only`：后续轮次仅发送 Playbook ID

通过环境变量 `PLAYBOOK_STRATEGY` 控制。

### 2. 结构化 LLM 沟通
- `structured_observation` 输出包含趋势、关键位、量价、形态、结论等结构化信息
- `signal_generation` 输出包含方向、入场、止损、理由的 JSON
- 便于后续 Sensors 和多轮分析复用

### 3. 智能多轮控制
通过 `quality_sensor` + `llm_critique` 共同判断是否继续下一轮，避免无效分析。

---

## 环境变量

| 变量                        | 默认值   | 说明 |
|-----------------------------|----------|------|
| `USE_MOCK_OBSERVATION`      | `true`   | 是否使用 Mock 数据 |
| `PLAYBOOK_STRATEGY`         | `full`   | Playbook 注入策略（`full` / `core`） |
| `TUSHARE_TOKEN`             | -        | Tushare 接口 Token |

---

## 测试

```bash
make test              # 运行所有测试
make test-cov          # 带覆盖率报告
```

---

## 注意事项

- **Tushare Token**：必须配置 `TUSHARE_TOKEN`
- **股票分钟数据**：需要 Tushare 分钟权限（部分用户可能无权限）
- **当前状态**：处于 DataProvider 重构 pilot 阶段，新旧逻辑并存
- **推荐**：日常开发使用 Mock 模式，验证真实数据时再切换

## 后续计划

- 完善股票分钟数据支持
- 将新 Provider 完全替换旧 `data_provider.py`
- 增加更多数据源（AkShare 等）

---

## License

MIT
=======
# ApexLi

> **Advanced Multi-Source DataProvider Trading Agent Framework**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Refactoring-orange)](https://github.com/adoocoke/eaagent/tree/refactor/data-provider)

ApexLi is a high-end trading intelligence framework built on **LangGraph**, delivering transparent, observable, and extensible multi-timeframe analysis for futures and equities through a
unified **DataProvider abstraction layer**.

---

## Project Overview

ApexLi provides a professional-grade foundation for building production-ready trading agents. By abstracting data access behind a clean `DataProvider` interface and `Factory` pattern, it
enables seamless switching between multiple data sources while maintaining strict engineering standards.

---

## ✨ Core Features

- **DataProvider + Factory Architecture** — Unified interface for all data sources with pluggable implementations
- **Multi-Source Support** — Tushare Futures, Tushare Stock, and Akshare Stock providers out of the box
- **Multi-Timeframe Data Extraction** — Daily, 30-minute, and 5-minute data with structured output
- **Deep LangGraph Integration** — Native support in `data_ingestion` nodes and graph execution
- **Production-Ready Engineering** — Comprehensive unit/integration tests, mock mode, and type safety

---

## 🏗️ Architecture

The `DataProvider` abstraction decouples trading logic from concrete data vendors:

```
DataProvider (ABC)
├── TushareFuturesProvider
├── TushareStockProvider
└── AkshareStockProvider
```

All providers are instantiated via:

```python
from eaagent.data_providers.factory import get_data_provider

provider = get_data_provider("tushare_futures")   # or "tushare_stock", "akshare_stock"
```

---

## 🚧 Current Status (refactor/data-provider)

This branch focuses exclusively on the **DataProvider refactoring effort**:

- ✅ Abstract base class + Factory pattern implemented
- ✅ TushareFuturesProvider, TushareStockProvider, AkshareStockProvider completed
- ✅ Initial integration into `data_ingestion` node
- ✅ Full test coverage for providers and factory
- 🔄 Active iteration — further Akshare enhancements and multi-timeframe optimizations in progress

---

## 🚀 Quick Start

```bash
git clone https://github.com/adoocoke/eaagent.git
cd eaagent
git checkout refactor/data-provider
pip install -e ".[dev]"
```

### Basic Usage

```python
from eaagent.data_providers.factory import get_data_provider

# Switch data sources effortlessly
futures_provider = get_data_provider("tushare_futures")
stock_provider   = get_data_provider("tushare_stock")
akshare_provider = get_data_provider("akshare_stock")

df = futures_provider.get_daily("RB2605.SHF", "2024-01-01", "2024-06-01")
```

---

## 🗺️ Roadmap

- Complete Akshare futures support
- Optimize multi-timeframe data ingestion pipeline
- Full migration from legacy data access layer

---

## License

MIT
