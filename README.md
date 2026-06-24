<div align="center">

# 🚀 ApexLi

**高级交易智能体框架**  
支持股票与期货的多数据源统一抽象层

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Enabled-FF6B6B)](https://github.com/langchain-ai/langgraph)
[![Status](https://img.shields.io/badge/Status-Refactoring-yellow)](https://github.com/adoocoke/ApexLi)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## ✨ 项目简介

**ApexLi** 是一个面向专业交易者的高级 AI Agent 框架，旨在通过统一的 **DataProvider 抽象层**，灵活接入多种数据源（Tushare、Akshare 等），并与 LangGraph 深度集成，实现股票与期货的多时间框架智能分析。

当前项目正处于 **DataProvider 架构重构** 阶段，目标是打造一个可扩展、高可观测、工程化程度高的交易分析系统。

---

## 🧩 核心特性

- 🔄 **多数据源统一抽象**：通过 `DataProvider` + `Factory` 模式，支持 Tushare（期货/股票）和 Akshare（股票）无缝切换
- 📊 **多时间框架分析**：支持日线 + 分钟线（5m/30m 等）结构化特征提取
- 🤖 **LangGraph 深度集成**：基于状态图构建可观测、可持久化的多轮分析流程
- 🧪 **工程化设计**：完整的单元测试 + Mock 支持，CI 自动化
- 🛡️ **Playbook 策略注入**：支持加载交易规则 playbook，实现规则驱动的分析

---

## 🏗️ 当前架构（重构中）

| 模块                    | 状态       | 说明                              |
|-------------------------|------------|-----------------------------------|
| `DataProvider` (抽象基类) | ✅ 已完成   | 统一接口定义                      |
| `TushareFuturesProvider`  | ✅ 已完成   | 期货数据支持                      |
| `TushareStockProvider`    | ✅ 已完成   | Tushare 股票数据支持              |
| `AkshareStockProvider`    | ✅ 已完成   | Akshare 股票数据支持              |
| `Factory`                 | ✅ 已完成   | 数据源工厂方法                    |
| `data_ingestion` 节点     | 🔄 重构中   | 已初步接入新 Provider             |
| 多时间框架特征提取        | 🔄 重构中   | 日线 + 分钟线支持完善中           |

---

## 🚀 快速开始

### 环境准备

```bash
git clone https://github.com/adoocoke/ApexLi.git
cd ApexLi
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,tushare,langgraph]"
```

### 运行分析（Mock 模式，推荐先体验）

```bash
python -m eaagent.a_plus_plus.graph
```

### 使用真实数据（Tushare）

```bash
USE_MOCK_OBSERVATION=false \
TUSHARE_TOKEN=your_token \
python -m eaagent.a_plus_plus.graph
```

### 使用 Akshare（股票）

```bash
USE_MOCK_OBSERVATION=false \
DATA_PROVIDER=akshare_stock \
python -m eaagent.a_plus_plus.graph
```

---

## 📍 当前状态

- ✅ DataProvider 抽象层已完成
- ✅ Tushare / Akshare Provider 已实现
- ✅ 与 LangGraph 初步集成
- 🔄 多时间框架数据获取与特征提取正在完善
- 🔄 可观测性（日志、颜色输出）持续优化

---

## 🗺️ 后续规划

- [ ] 完善多时间框架数据获取（尤其是 Tushare 分钟线）
- [ ] 优化 Akshare 股票数据稳定性
- [ ] 加强 Prompt 可观测性（完整打印 LLM 沟通过程）
- [ ] 节点模块化拆分（提高可维护性）
- [ ] 支持更多数据源（聚宽、米筐等）

---

## 📁 关键目录结构

```
eaagent/
├── data_providers/              # 数据源抽象层（核心）
│   ├── base.py
│   ├── tushare_futures.py
│   ├── tushare_stock.py
│   ├── akshare_stock.py
│   └── factory.py
├── a_plus_plus/
│   ├── graph.py
│   └── nodes/                   # LangGraph 节点
└── tests/
    ├── unit/
    └── integration/
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

当前重点方向：
- DataProvider 稳定性与扩展性
- 多时间框架分析能力
- Agent 可观测性与调试体验

---

**注意**：本项目仍处于快速迭代阶段，API 可能会有调整。

---

<div align="center">

**Made with ❤️ by adoocoke**

</div>
