# ApexLi

> **Advanced Multi-Source DataProvider Trading Agent Framework**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/Status-Refactoring-orange)](https://github.com/adoocoke/eaagent/tree/refactor/data-provider)

ApexLi is a high-end trading intelligence framework built on **LangGraph**, delivering transparent, observable, and extensible multi-timeframe analysis for futures and equities through a unified **DataProvider abstraction layer**.

---

## Project Overview

ApexLi provides a professional-grade foundation for building production-ready trading agents. By abstracting data access behind a clean `DataProvider` interface and `Factory` pattern, it enables seamless switching between multiple data sources while maintaining strict engineering standards.
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
# test trigger
